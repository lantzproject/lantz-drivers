from lantz import Driver, Feat, DictFeat, Action

import ctypes as ct

from ctypes import c_char_p, c_void_p, c_int, c_double, POINTER, byref, create_string_buffer

from collections import Iterable, OrderedDict


class PhotonEtcComm():


    def __init__(self):

        # this should point to the location of the DLL
        dll_loc = 'D:\\Code\\Github\\lantz\\lantz\\drivers\\photonetc\\PE_Filter_SDK.dll'
        self.config_dir = 'C:\\Program Files (x86)\\Photon etc\\PHySpecV2\\Devices\\'


        # Uses WinDLL to load the dll file
        self.lib = ct.WinDLL(dll_loc)

        # Here, we set up the argument types for the varios functions
        # encapsulated in the DLL. All these are essentially taken from the
        # header file PE_Filter.h

        # Functions necessary for setting up PE filter class
        self.lib.PE_Create.argtypes = [c_char_p, c_void_p]
        self.lib.PE_Destroy.argtypes = [c_void_p]

        self.lib.PE_GetSystemCount.argtypes = [c_void_p]
        self.lib.PE_GetSystemName.argtypes = [c_void_p, c_int, c_char_p, c_int]

        self.lib.PE_GetStatusStr.argtypes = [c_int]

        # These filters are used for interacting with a single filter moodule.
        self.lib.PE_Open.argtypes = [c_void_p, c_char_p]
        self.lib.PE_Close.argtypes = [c_void_p]

        self.lib.PE_GetWavelength.argtypes = [c_void_p, POINTER(c_double)]
        self.lib.PE_SetWavelength.argtypes = [c_void_p, c_double]

        # These settings enable control of ome of the more advanced settings/
        # options, and the different gratings present in the filter.
        self.lib.PE_GetWavelengthRange.argtypes = [c_void_p, POINTER(c_double), POINTER(c_double)]
        self.lib.PE_HasHarmonicFilter.argtypes = [c_void_p]

        self.lib.PE_GetHarmonicFilterEnabled.argtypes = [c_void_p, POINTER(c_int)]
        self.lib.PE_SetHarmonicFilterEnabled.argtypes = [c_void_p, c_int]

        self.lib.PE_GetGratingCount.argtypes = [c_void_p, POINTER(c_int)]
        self.lib.PE_GetGratingCount.argtypes = [c_void_p, c_int, c_char_p, c_int]
        self.lib.PE_GetGratingWavelengthRange.argtypes = [c_void_p, c_int, POINTER(c_double), POINTER(c_double)]
        self.lib.PE_GetGratingWavelengthExtendedRange.argtypes = [c_void_p, c_int, POINTER(c_double), POINTER(c_double)]

        self.lib.PE_SetWavelengthOnGrating.argtypes = [c_void_p, c_int, c_double]
        self.lib.PE_GetGrating.argtypes = [c_void_p, POINTER(c_int)]



    def __del__(self):
        """
        Calls C garbage collection methods from Python in order to close the LLTF
        communication module, and avoid issues with recollecting.
        """
        #self.destroy()

    def getLibraryVersion(self):
        """
        Returns the version of the library used by the software.
        """
        value =  hex(self.lib.PE_GetLibraryVersion())

        # code to decode bit shifted string into version
        major = int(value[2:-4], 16)
        minor = int(value[-4:-2], 16)
        bugfix = int(value[-2:], 16)
        return '{}.{}.{}'.format(major, minor, bugfix)


    def create(self, system):
        """
        Creates a handle for the filter described in "system".xml configuration file.
        """

        xml_filename = self.config_dir + system + '.xml'

        # create pointer to serve as system handle
        pe_handle = c_void_p()

        # encode configuration filename, pass reference to system handle
        status = self.lib.PE_Create(xml_filename.encode(), byref(pe_handle))

        return pe_handle, status

    def destroy(self, pe_handle):
        """
        Destroys the filter handle, for garbage collection purposes.
        """
        status = self.lib.PE_Destroy(pe_handle)
        return status


    def getSystemName(self, pe_handle, index=0):
        """

        """
        size = 256
        systemname = create_string_buffer(size)

        status = self.lib.PE_GetSystemName(pe_handle, index, systemname, size)

        return systemname.value.decode('utf-8'), status


    def openSystem(self, pe_handle, systemname):

        status = self.lib.PE_Open(pe_handle, systemname.encode())
        return status

    def closeSystem(self, pe_handle):

        status = self.lib.PE_Close(pe_handle)
        return status


    def getWavelength(self, pe_handle):

        wavelength = c_double()

        status = self.lib.PE_GetWavelength(pe_handle, byref(wavelength))

        return wavelength.value, status

    def setWavelength(self, pe_handle, wavelength):

        status = self.lib.PE_SetWavelength(pe_handle, wavelength)

        return status


    def getWavelengthRange(self, pe_handle):

        min_wavelength = c_double()
        max_wavelength = c_double()

        status = self.lib.PE_GetWavelengthRange(pe_handle, byref(min_wavelength), byref(max_wavelength))

        return (min_wavelength.value, max_wavelength.value), status



    def statusCode(self, code):
        """
        Implements lookup table for status codes. Note that these must be kept
        up to date with any changes that may occur in the C header file, since
        they are currently hard coded here and do not draw from PE_filter.h!
        """

        # this doesn't seem to work - not sure why, but appears to return garbage.
        #self.lib.PE_GetStatusStr(code)

        STATUS_CODES = {
            0: 'Successful operation',
            1: 'Invalid handle: handle already deleted or null',
            2: 'PE Failure: instrument communication failure',
            3: 'Configuration file is missing.',
            4: 'Configuration file invalid.',
            5: 'Invalid wavelength.',
            6: 'Missing harmonic filter: no harmonic filter present in system.',
            7: 'Invalid filter: requested filter does not exist.',
            8: 'Unknown status',
            9: 'Invalid grating: requested grating does not exist',
            10: 'Invalid buffer: null buffer',
            11: 'Unsupported filter configuration.',
            12: 'Filter connection error: no filter is connected.'
        }
        #status_str = self.lib.PE_GetStatusStr(code)

        return STATUS_CODES[code]



class PhotonEtcFilter(Driver):

    def initialize(self):
        """
        Creates the library for communicating with the tunable filter.
        """
        self.comm = PhotonEtcComm()

        self.filters = {}

    def add_filter(self, system_name, index=0, user_name=None):
        """
        Connects to the filter at system_name, index to the system.
        """

        if not user_name:

            user_name = system_name

        # create PE_Filter
        pe_handle, status = self.comm.create(system_name)

        # get filter name at index
        name, status = self.comm.getSystemName(pe_handle, index)

        # open connection to the system
        status = self.comm.openSystem(pe_handle, name)

        self.filter_info = {'name': system_name,
                            'wavelength_range': self.comm.getWavelengthRange(pe_handle)[0],
                            'user_name': user_name,
                            'handle': pe_handle}

        self.filters[user_name] = self.filter_info

        print(self.filter_info)

    def remove_filter(self, filter_name):
        """
        Removes the specified filter to avoid memory leak issues.
        """
        status = self.comm.closeSystem(filter_name['handle'])

        if len(list(self.filters.keys())) == 0:
            status = self.comm.destroy(filter_name['handle'])

        return status

    def finalize(self):
        """
        Closes the connections to PE filters and the PE filter library.
        """
        for key in list(self.filters.keys()):

            f = self.filters.pop(key)
            print('Closing time!')
            self.remove_filter(f)

    @Feat(read_once=True)
    def lib_verision(self):
        """
        Test code to check library version.
        """
        return self.comm.getLibraryVersion()

    @DictFeat(units='nm')#, keys=FILTERS)
    def wavelength(self, filter_name):
        """
        Returns the filter wavelength in nanometers. Prints an error message
        if the returned value lies outside the filter range.
        """
        handle = self.filters[filter_name]['handle']

        wavelength, status = self.comm.getWavelength(handle)

        min_nm, max_nm = self.wavelength_range['IR']

        if min_nm <= wavelength <= max_nm:

            return wavelength

        print('Invalid wavelength {}nm for {}, must lie between {}nm and {}nm'.format(wavelength, filter_name, min_nm, max_nm))

    @wavelength.setter
    def wavelength(self, filter_name, nm):
        """
        Sets the filter wavelength to be nm (in nanometers). Includes bounds
        checking to ensure that the set wavelength falls within the range
        supported by the filter.
        """

        handle = self.filters[filter_name]['handle']

        min_nm, max_nm = self.wavelength_range[filter_name]

        if min_nm <= nm <= max_nm:

            return self.comm.setWavelength(handle, nm)

        print('Invalid wavelength {}nm for {}, must lie between {}nm and {}nm'.format(nm, filter_name, min_nm, max_nm))


    @DictFeat(read_once = True)
    def wavelength_range(self, filter_name):
        """
        Returns the wavelength range of the specified filter.
        """
        handle = self.filters[filter_name]['handle']

        wavelength_range, status = self.comm.getWavelengthRange(handle)
        return wavelength_range



def test():
    # test script tries to implement example code found in SDK manual as proof
    # of concept through lantz interface w/ DictFeat structure to handle
    # multiple filters at a single time.

    ## TODO: test code and see if it can support simultaneous control of both
    # filters without issues.

    lltf = PhotonEtcFilter()
    lltf.initialize()

    print('Library version: {}'.format(lltf.lib_verision))

    system_list = ['M000010133']  #,'M000010161']
    filter_name = 'IR'

    for f in system_list:

        lltf.add_filter(f, user_name=filter_name)

        print('Wavelength range: {}'.format(lltf.wavelength_range[filter_name]))

        print('Wavelength: {}'.format(lltf.wavelength[filter_name]))

        lltf.wavelength[filter_name] = 850.0

        print('Wavelength: {}'.format(lltf.wavelength[filter_name]))
        lltf.wavelength[filter_name] = 950.0

        print('Wavelength: {}'.format(lltf.wavelength[filter_name]))

        lltf.wavelength[filter_name] = 2400.0

        print('Wavelength: {}'.format(lltf.wavelength[filter_name]))

        # this should print an error message
        lltf.wavelength[filter_name] = 400.0

    lltf.finalize()




if __name__ == "__main__":
    test()
