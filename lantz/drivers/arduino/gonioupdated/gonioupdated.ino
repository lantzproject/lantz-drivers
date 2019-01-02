#include "TimerOne.h"
///Set to one for more Serial consol prints
const int debug = 0;
/// Pin definitions
const int pulPins[] = {6, 8, 4};
const int dirPins[] = {5, 7, 11};
const int encoderAP = 3;
const int encoderBP = 12;
const int switchPin = 2;
/// Constants
const float pi = 3.14159265;
const float RadtoDeg = 57.2957795;
const float axis0DegtoSteps = 0.00035155;
const float axis1DegtoSteps = 0.00079069;
const float axis2Conversion = 3200;
const long initial_pos[] = {0L,113825L, 0L};
/// Limits for the different values
const float THETA_LIMITS[] = {70., 115.};
const float PHI_LIMITS[]   = {30., 180.};
const float ALPHA_LIMITS[] = {-100., 21.};
const float BETA_LIMITS[]  = {-135., 135.};
const int PERIOD_LIMITS[] = {20, 500};
const float R_LIMITS[] = {-100,100};
/// Global Vars
int axis_increment[]  = {1, 1, 1};
long axis_remainder[] = {0, 0, 0};
int pinDelay[] = {50, 50, 100};
//int pinDelay = {50, 50, 100}
long steps[] = {0L,113825L, 0L};
int switch_state = 0;
///System state
///   0:  Ready
///   1:  Moving
///   2:  Emergency Stop
int run_state = 0;
int unlock = 0;
String input;
///--------------------------------------------------------------------------------------------
///                   High Level Commands
///--------------------------------------------------------------------------------------------
///Returns values
///     -1:  theta or phi were out of bounds
///     -2:  alpha or beta were out of bounds
///     -3:  attempted rotateTo while run_state != 0
///     -4:  period is out of bound
///     -8:  emergency stop
///     -9:  raxis is out of bounds
///    -10:  Unknown cmd
///    -11:  other error
///    -50:  no error
/// Get alpha, beta
/// theta     = 0
/// phi       = 1
float get_sphere(int angle){
  float alpha = float(steps[0]) * axis0DegtoSteps / RadtoDeg;
  float beta = float(steps[1])* axis1DegtoSteps / RadtoDeg;
  float theta;
  float phi;
  int ret = motor2spher(alpha, beta, theta, phi);
  if (angle == 0){
    return theta;
  }
  else {
    return phi;
  }
}
/// Get theta from alpha and beta
float get_theta(){
  float ret = get_sphere(0);
  return ret;
}
/// Get phi from alpha and beta
float get_phi(){
  float ret = get_sphere(1);
  return ret;
}
/// Relative rotation
int rrot(int axis, long relSteps){
  return relativeRotate(axis, relSteps);
}
/// Absolute rotation
int arot(int axis, long absSteps){
  return absoluteRotate(axis, absSteps);
}
/// Absolute move in spherical coordinates
int asphere(float theta, float phi){
  float alpha, beta;
  float ret;
  ret = spher2motorangles(theta, phi, alpha, beta);
  if (ret == -50){
    ret = rotateTo(alpha, beta);
  }
  return ret;
}
/// Set theta, keep phi the same
int set_theta(float theta){
  float delta = 0.001;
  float phi = get_phi();
  float theta_init = get_theta();
  if (theta_init <= theta + delta && theta_init >= theta - delta){
    run_state == 0;
    return -50;
  }
  else {
    int ret = asphere(theta, phi);
    return ret;
  }
}
/// Set phi, keep theta the same
int set_phi(float phi){
  float delta = 0.001;
  float theta = get_theta();
  float phi_init = get_phi();
  if (phi_init <= phi + delta && phi_init >= phi - delta){
    run_state == 0;
    return -50;
  }
  else {
  int ret = asphere(theta, phi);
    return ret;
  }
}
int set_R(float abs_r){
  if (valid_raxis(abs_r)){
    return absoluteRotate(2, abs_r*axis2Conversion);
  }
  else{
    return -9;
  }
  
}
/// Relative move in spherical coordinates
int rel_R(float rel_r){
  return relativeRotate(2, rel_r*axis2Conversion);
}
///Set the interupt delay in us
int pperiod(int axis, int period){
  if (period < PERIOD_LIMITS[0] or period > PERIOD_LIMITS[1])
  {
    return -4;
  }
  else{
    pinDelay[axis] = period;
    Timer1.stop();
    Timer1.initialize(pinDelay[axis]);
    Timer1.start();
    return -50;
  }
}
int stop_move(){
  Timer1.stop();
  run_state = 0;
  axis_remainder[0] = 0;
  axis_remainder[1] = 0;
  axis_remainder[2] = 0;
  return -50;
}
int get_state(){
  return run_state;
}
///--------------------------------------------------------------------------------------------
///                   Main Code Logic
///--------------------------------------------------------------------------------------------
void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 3; i++) {
    Timer1.initialize(pinDelay[i]);
  }
  Timer1.stop();
  Timer1.attachInterrupt(ISR_rotate);
  while (Serial.available() > 0) {
    Serial.read();
  }
  for (int i = 0; i < (sizeof(pulPins) / sizeof(int)); i++) {
    pinMode(pulPins[i], OUTPUT);
    digitalWrite(pulPins[i], LOW);
  }
  for (int i = 0; i < (sizeof(dirPins) / sizeof(int)); i++) {
    pinMode(dirPins[i], OUTPUT);
    digitalWrite(pulPins[i], LOW);
  }
  pinMode(encoderAP, INPUT_PULLUP);
  //digitalWrite(encoderAP, HIGH);
  pinMode(encoderBP, INPUT_PULLUP);
  //digitalWrite(encoderBP, HIGH);
  pinMode(switchPin, INPUT);
  digitalWrite(switchPin, HIGH);
  return;
}
void loop() {
  if (Serial.available() > 0) {
   exec_cmd();
  }
}
///Decide what to execute
void exec_cmd(){
  ///Parse Input
  input = Serial.readStringUntil('\n');
  input.toLowerCase();
  input.trim();
  int space1 = input.indexOf(' ');
  int space2 = input.indexOf(' ', space1 + 1);
  String cmd = input.substring(0, space1);
  String arg1 = input.substring(space1 + 1, space2);
  String arg2 = input.substring(space2);
  //Exec Cmd
  int ret;
  if (cmd == "rot?") {
    Serial.println(getSteps(arg1.toInt()));
    ret = -50;
  }
  else if (cmd == "rrot") {
    ret = rrot(arg1.toInt(), arg2.toInt());
    Serial.println(0);
  }
  else if (cmd == "zero") {
    ret = zero(arg1.toInt());
    Serial.println(0);
  }
  else if (cmd == "arot") {
    ret = arot(arg1.toInt(), arg2.toInt());
    Serial.println(0);
  }
  else if (cmd == "asphere"){
    ret = asphere(arg1.toFloat(), arg2.toFloat());
    Serial.println(0);
  }
  else if (cmd == "theta"){
    ret = set_theta(arg1.toFloat());
    Serial.println(0);
  }
  else if (cmd == "phi"){
    ret = set_phi(arg1.toFloat());
    Serial.println(0);
  }
  else if (cmd == "rabs"){
    ret = set_R(arg1.toFloat());
    Serial.println(0);
  }
  else if (cmd == "rrel"){
    ret = rel_R(arg1.toFloat());
    Serial.println(0);
  }
  else if (cmd == "raxis?"){
    Serial.println(getSteps(2)/axis2Conversion);
    ret = -50;
  }
  else if (cmd == "period?"){
    Serial.println(pinDelay[arg1.toInt()]);
    ret = -50;
  }
  else if (cmd == "pperiod"){
    ret = pperiod(arg1.toInt(), arg2.toInt());
    Serial.println(0);
  }
  else if (cmd == "stop"){
    ret = stop_move();
    Serial.println(0);
  }
  else if (cmd == "unlock"){
    unlock = 1;
    run_state = 0;
    Serial.println(0);
    ret = -50;
  }
  else if (cmd == "lock"){
    unlock = 0;
    Serial.println(0);
    ret = -50;
  }
  else if (cmd == "switch?"){
    Serial.println(unlock);
    ret = -50;
  }
  else if (cmd == "state?"){
    Serial.println(get_state());
    ret = -50;
  }
  else if (cmd == "sphere?") {
    Serial.println(String(get_theta())+","+String(get_phi()));
    ret = -50;
  }
  else if (cmd == "theta?") {
    Serial.println(get_theta());
    ret = -50;
  }
  else if (cmd == "phi?") {
    Serial.println(get_phi());
    ret = -50;
  }
  else{
    Serial.println(0);
    ret = -10;
  }
  Serial.println(ret);
  return;
}
///--------------------------------------------------------------------------------------------
///                   Low-level Helper functions
///--------------------------------------------------------------------------------------------
///From theta and phi in degrees, returns alpha and beta
///Returns values
///     -1:  if the theta or phi were out of bounds
///     -2:  if the alpha or beta were out of bounds
///     -3:  other error
///      0:  no error
int motor2spher(float alpha, float beta, float &theta, float &phi) {
  float thetaRad = acos(sin(alpha) * sin(beta));
  float phiRad = acos(cos(beta) / sin(thetaRad));
  theta = thetaRad * RadtoDeg;
  phi = phiRad * RadtoDeg;
  return -50;
}
int spher2motorangles(float theta, float phi, float &alpha, float &beta){
  float delta = 0.000001;
  if (valid_theta_phi(theta, phi)) {
    float cos_b = cos(phi / RadtoDeg) * sin(theta / RadtoDeg);
    if (abs(cos_b-1)<delta){
      if (debug){Serial.println("Converting to fix 0, 0");}
      if (valid_alpha_beta(0., 0.)){
        alpha = 0;
        beta  = 0;
        return -50;
      }
      else{
        if (debug){Serial.println("alpha or beta out of bounds");}
        return -2;
      }
    }
    else if(abs(cos_b+1)<delta){
      if (debug){Serial.println("Not Implemented");}
      return -10;
    }
    else{
      float quotient = cos(theta / RadtoDeg) / sin(acos(cos_b));
      if (quotient >= -1 && quotient <= 1) {
        float a = asin(quotient)* RadtoDeg;
        float b = acos(cos_b)* RadtoDeg;
        if (debug){Serial.println(a);}
        if (debug){Serial.println(b);}
        if (valid_alpha_beta(a, b)){
          alpha = a;
          beta  = b;
        return -50;
        }
        else{
          if (debug){Serial.println("alpha or beta out of bounds");}
          return -2;
        }
        return -50;
      }
      else{
        if (debug){Serial.println("quotient was outside [-1, 1]");}
        return -3;
      }
    }
  }
  else {
    if (debug){Serial.println("Out of bound conversion");}
    return -1;
  }
}
/// Returns True if the angles are valid
bool valid_alpha_beta(float alpha, float beta){
  return (alpha >= ALPHA_LIMITS[0] && alpha <= ALPHA_LIMITS[1] && beta >= BETA_LIMITS[0] && beta <= BETA_LIMITS[1]);
}
/// Returns True if the angles are valid
bool valid_theta_phi(float theta, float phi){
  return (theta >= THETA_LIMITS[0] && theta <= THETA_LIMITS[1] && phi >= PHI_LIMITS[0] && phi <= PHI_LIMITS[1]);
}
bool valid_raxis(float r){
  return (r >= R_LIMITS[0] && r <= R_LIMITS[1]);
}
int rotateTo(float alpha, float beta){
  if (run_state == 0){
    if (valid_alpha_beta(alpha, beta)){
      absoluteRotate(0, alpha / axis0DegtoSteps);
      absoluteRotate(1, beta  / axis1DegtoSteps);
      return -50;
    }
    else{
      return -2;
    }
  }
  else{
    return -3;
  }
}
/// Get alpha, beta
/// alpha = 0
/// beta  = 1
/// R     = 2
long getSteps(int axis) {
  return steps[axis];
}
int relativeRotate(int axis, long relSteps) {
  setup_rotate(axis, relSteps);
  return -50;
}
int absoluteRotate(int axis, long absSteps) {
  long relSteps = absSteps - steps[axis];
  relativeRotate(axis, relSteps);
  return -50;
}
int zero(int axis) {
  steps[axis] = initial_pos[axis];
  return -50;
}
void setup_rotate(int axis, long target_steps){
  Timer1.stop();
  ///Setup motion direction
  if (target_steps < 0) {
    axis_increment[axis] = -1;
    digitalWrite(dirPins[axis], LOW);
  } else {
    axis_increment[axis] = 1;
    digitalWrite(dirPins[axis], HIGH);
  }
  /// Setup number of steps
  axis_remainder[axis]=abs(target_steps);
  Timer1.start();
  run_state = 1;
}
void ISR_rotate(){
  int state = 0;
  int sPin = digitalRead(switchPin);
  if (sPin == LOW){
    switch_state++;
  }
  else {
    switch_state = 0;
  }
  if (switch_state <= 4 or unlock != 0){
    for (int i = 0; i < 3 ; i++) {
    
      if (axis_remainder[i]>0){
        state = digitalRead(pulPins[i]);
        digitalWrite(pulPins[i],  state^ 1);
        
        if (state == HIGH){
          axis_remainder[i]--;
          steps[i] = steps[i] + axis_increment[i];
        }
    }
  }
    if (axis_remainder[0]<=0 and axis_remainder[1]<=0 and axis_remainder[2]<=0){
      stop_move();
  }
  }
  
  else {
    stop_move();
    run_state = 0;
  }
}

