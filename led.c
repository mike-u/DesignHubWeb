#include <wiringPi.h>
#include <stdio.h>
 
#define  LEDPin    0
 
int main(void)
{
  if(wiringPiSetup() == -1){//when the wiringPi initialization fails, print message to the screen.
    printf("setup wiringPi failed !");
    return 1;
  }
 
  pinMode(LEDPin, OUTPUT);
 
  while(1){
    digitalWrite(LEDPin, LOW);   //led on
    printf("led on...\n");
    delay(500);
    digitalWrite(LEDPin, HIGH);  //led off
    printf("...led off\n");
    delay(500);
  }
  return 0;
}