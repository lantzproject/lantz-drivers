# -*- coding: utf-8 -*-
"""
    lantz.drivers.alliedvision
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation for a alliedvision camera via pymba and pylon

    Requires:
    - pymba: https://github.com/morefigs/pymba
    - vimba: https://www.alliedvision.com/en/products/software.html

    Log:
    - create same API as lantz.drivers.basler


    Author: Vasco Tenner
    Date: 20181204

    TODO:
    - Test
    - 12 bit packet readout
    - Bandwith control
    - Dynamically set available values for feats
"""

from lantz.driver import Driver
from lantz import Feat, DictFeat, Action
from pymba import Vimba
import numpy as np
import threading
import time


beginner_controls = ['ExposureTimeAbs', 'GainRaw', 'Width', 'Height',
                     'OffsetX', 'OffsetY']
aliases = {'exposure_time': 'ExposureTimeAbs',
           'gain': 'GainRaw',
          }


def todict(listitems):
    'Helper function to create dicts usable in feats'
    d = {}
    for item in listitems:
        d.update({item: item})
    return d


def attach_dyn_propr(instance, prop_name, propr):
    """Attach property proper to instance with name prop_name.

    Reference:
    * https://stackoverflow.com/a/1355444/509706
    * https://stackoverflow.com/questions/48448074
    """
    class_name = instance.__class__.__name__ + 'C'
    child_class = type(class_name, (instance.__class__,), {prop_name: propr})

    instance.__class__ = child_class


def create_getter(p):
    def tmpfunc(self):
        return self.cam[p]
    return tmpfunc


def create_setter(p):
    def tmpfunc(self, val):
        self.cam[p] = val
    return tmpfunc


def list_cameras():
    with Vimba() as vimba:
        # get system object
        system = vimba.getSystem()

        # list available cameras (after enabling discovery for GigE cameras)
        if system.GeVTLIsPresent:
            system.runFeatureCommand("GeVDiscoveryAllOnce")
            time.sleep(0.2)
        cameraIds = vimba.getCameraIds()
        for cameraId in cameraIds:
            print(cameraId)


class VimbaCam(Driver):

    def __init__(self, camera=0, level='beginner',
                 *args, **kwargs):
        """
        @params
        :type camera_num: int, The camera device index: 0,1,..
        :type level: str, Level of controls to show ['beginner', 'expert']

        Example:
        import lantz
        from lantz.drivers.alliedvision import Cam
        import time
        try:
                lantzlog
        except NameError:
                lantzlog = lantz.log.log_to_screen(level=lantz.log.DEBUG)

        cam = Cam(camera='Basler acA4112-8gm (40006341)')
        cam.initialize()
        cam.exposure_time
        cam.exposure_time = 3010
        cam.exposure_time
        cam.grab_image()
        print('Speedtest:')
        nr = 10
        start = time.time()
        for n in range(nr):
            cam.grab_image()
            duration = (time.time()-start)*1000*lantz.Q_('ms')
            print('Read {} images in {}. Reading alone took {}. Framerate {}'.format(nr,
                duration, duration - nr* cam.exposure_time, nr / duration.to('s')))
        cam.finalize()
        """
        super().__init__(*args, **kwargs)
        self.camera = camera
        self.level = level
        # Some actions cannot be performed while reading
        self._grabbing_lock = threading.RLock()

    def initialize(self):
        """
        Params:
        camera -- number in list of show_cameras or friendly_name
        """

        self.vimba = Vimba()
        self.vimba.startup()

        cameras = self.vimba.getCameraIds()
        self.log_debug('Available cameras are:' + str(cameras))

        try:
            if isinstance(self.camera, int):
                cam = cameras[self.camera]
                self.cam = self.vimba.getCamera(cam)
            else:
                self.cam = self.vimba.getCamera(self.camera)
        except RuntimeError as err:
            self.log_error(err)
            raise RuntimeError(err)

        self.frame = self.cam.getFrame()
        self.frame.announceFrame()
        self.cam.startCapture()

        self._dynamically_add_properties()
        self._aliases()

        # get rid of Mono12Packed and give a log error:
        fmt = self.pixel_format
        if fmt == str('Mono12Packed'):
            self.log_error('PixelFormat {} not supported. Using Mono12 '
                           'instead'.format(fmt))
            self.pixel_format = 'Mono12'

        # Go to full available speed
        # cam.properties['DeviceLinkThroughputLimitMode'] = 'Off'

    def finalize(self):
        self.cam.endCapture()
        self.cam.revokeAllFrames()
        return

    def _dynamically_add_properties(self):
        """Add all properties available on driver as Feats"""
        props = self.getFeatureNames() if self.level == 'expert' else beginner_controls
        for p in props:
            info = self.cam.getFeatureInfo(p)
            range_ = self.cam.getFeatureRange(p)
            limits = range_ if isinstance(tuple, range_) else None
            values = range_ if isinstance(list, range_) else None

            feat = Feat(fget=create_getter(p),
                        fset=create_setter(p),
                        doc=info.description,
                        units=info.unit,
                        limits=limits,
                        values=values,
                        )
            feat.name = p
            attach_dyn_propr(self, p, feat)

    def _aliases(self):
        """Add easy to use aliases to strange internal pylon names

        Note that in the Logs, the original is renamed to the alias"""
        for alias, orig in aliases.items():
            attach_dyn_propr(self, alias, self.feats[orig].feat)

    @Feat()
    def info(self):
        # We can still get information of the camera back
        return 'Camera info of camera object:', self.cam.getInfo()  # TODO TEST

    # Most properties are added automatically by _dynamically_add_properties

    @Feat(values=todict(['Mono8', 'Mono12', 'Mono12Packed']))
    def pixel_format(self):
        fmt = self.cam['PixelFormat']
        if fmt == 'Mono12Packed':
            self.log_error('PixelFormat {} not supported. Use Mono12 instead'
                           ''.format(fmt))
        return fmt

    @pixel_format.setter
    def pixel_format(self, value):
        if value == 'Mono12Packed':
            self.log_error('PixelFormat {} not supported. Using Mono12 '
                           'instead'.format(value))
            value = 'Mono12'
        self.cam['PixelFormat'] = value

    @Feat()
    def properties(self):
        """Dict with all properties supported by pylon dll driver"""
        return self.cam.getFeatureNames()

    @Action()
    def list_properties(self):
        """List all properties and their values"""
        for key in self.cam.getFeatureNames():
            try:
                value = self.cam[key]
            except IOError:
                value = '<NOT READABLE>'

            description = self.cam.getFeatureInfo(key)
            range_ = self.cam.getFeatureRange(key)
            print('{0} ({1}):\t{2}\t{3}'.format(key, description, value, range_))

    @Action(log_output=False)
    def grab_image(self):
        """Record a single image from the camera"""
        self.cam.AcquisitionMode = 'SingleFrame'
        try:
            self.frame.queueFrameCapture()
            success = True
        except:
            success = False

        self.cam.runFeatureCommand('AcquisitionStart')
        self.cam.runFeatureCommand('AcquisitionStop')
        self.frame.waitFrameCapture(0)
        frame_data = self.frame.getBufferByteData()
        if success:
            img_config = {
                'buffer': frame_data,
                'dtype': np.uint8,
                'shape': (self.frame.height, self.frame.width, 1),
            }
            img = np.ndarray(**img_config)
            return img[..., 0]
        else:
            return None

    @Action(log_output=False)
    def grab_images(self, num=1):
        # ΤΟDO see https://gist.github.com/npyoung/1c160c9eee91fd44c587
        raise NotImplemented()
        with self._grabbing_lock:
            img = self.cam.grab_images(num)
        return img

    @Action(log_output=False)
    def getFrame(self):
        """Backward compatibility"""
        return self.grab_image

    @Action()
    def set_roi(self, height, width, yoffset, xoffset):
        # Validation:
        if width + xoffset > self.properties['WidthMax']:
            self.log_error('Not setting ROI:  Width + xoffset = {} exceeding '
                           'max width of camera {}.'.format(width + xoffset,
                                                            self.properties['WidthMax']))
            return
        if height + yoffset > self.properties['HeightMax']:
            self.log_error('Not setting ROI: Height + yoffset = {} exceeding '
                           'max height of camera {}.'.format(height + yoffset,
                                                             self.properties['HeightMax']))
            return

        # Offset should be multiple of 2:
        xoffset -= xoffset % 2
        yoffset -= yoffset % 2

        if height < 16:
            self.log_error('Height {} too small, smaller than 16. Adjusting '
                           'to 16'.format(height))
            height = 16
        if width < 16:
            self.log_error('Width {} too small, smaller than 16. Adjusting '
                           'to 16'.format(width))
            width = 16

        with self._grabbing_lock:
            # Order matters!
            if self.OffsetY > yoffset:
                self.Height = height
                self.OffsetY = yoffset
            else:
                self.Height = height
                self.OffsetY = yoffset
            if self.OffsetX > xoffset:
                self.OffsetX = xoffset
                self.Width = width
            else:
                self.Width = width
                self.OffsetX = xoffset

    @Action()
    def reset_roi(self):
        """Sets ROI to maximum camera size"""
        self.set_roi(self.properties['HeightMax'],
                     self.properties['WidthMax'],
                     0,
                     0)

    # Helperfunctions for ROI settings
    def limit_width(self, dx):
        if dx > self.properties['WidthMax']:
            dx = self.properties['WidthMax']
        elif dx < 16:
            dx = 16
        return dx

    def limit_height(self, dy):
        if dy > self.properties['HeightMax']:
            dy = self.properties['HeightMax']
        elif dy < 16:
            dy = 16
        return dy

    def limit_xoffset(self, xoffset, dx):
        if xoffset < 0:
            xoffset = 0
        if xoffset + dx > self.properties['WidthMax']:
            xoffset = self.properties['WidthMax'] - dx
        return xoffset

    def limit_yoffset(self, yoffset, dy):
        if yoffset < 0:
            yoffset = 0
        if yoffset + dy > self.properties['HeightMax']:
            yoffset = self.properties['HeightMax'] - dy
        return yoffset

    @Action()
    def calc_roi(self, center=None, size=None, coords=None):
        """Calculate the left bottom corner and the width and height
        of a box with center (x,y) and size x [(x,y)]. Respects device
        size"""
        if center and size:
            y, x = center
            try:
                dy, dx = size
            except TypeError:
                dx = dy = size

            # Make sizes never exceed camera sizes
            dx = self.limit_width(dx)
            dy = self.limit_width(dy)

            xoffset = x - dx // 2
            yoffset = y - dy // 2

            xoffset = self.limit_xoffset(xoffset, dx)
            yoffset = self.limit_yoffset(yoffset, dy)

            return dy, dx, yoffset, xoffset

        elif coords:
            xoffset = int(coords[1][0])
            dx = int(coords[1][1] - xoffset)

            yoffset = int(coords[0][0])
            dy = int(coords[0][1] - yoffset)

            # print(dy,dx)
            dx = self.limit_width(dx)
            dy = self.limit_height(dy)

            # print(yoffset, xoffset)
            xoffset = self.limit_xoffset(xoffset, dx)
            yoffset = self.limit_yoffset(yoffset, dy)

            return dy, dx, yoffset, xoffset

        else:
            raise ValueError('center&size or coords should be supplied')

    def calc_roi_from_rel_coords(self, relcoords):
        """Calculate the new ROI from coordinates relative to the current
        viewport"""

        coords = ((self.OffsetY + relcoords[0][0],
                   self.OffsetY + relcoords[0][1]),
                  (self.OffsetX + relcoords[1][0],
                   self.OffsetX + relcoords[1][1]))
        # print('Rel_coords says new coords are', coords)
        return self.calc_roi(coords=coords)