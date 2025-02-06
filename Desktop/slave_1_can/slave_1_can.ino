#include <AS5600.h>
#include <AccelStepper.h>
#include <Wire.h>



#define dir 4
#define pul 3

AS5600 enc1;
AccelStepper stepper1(AccelStepper::DRIVER, pul,dir);


float setaspeed(float accelera, float maxspeed) {
    stepper1.setMaxSpeed(maxspeed);
    stepper1.setAcceleration(accelera);

}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  enc1.begin();
  setaspeed(150,200);
}



void loop() {
  stepper1.moveTo(30);
  while (stepper1.distanceToGo() != 0)
    {
      Serial.println("selaaam");
      stepper1.run();

}
}