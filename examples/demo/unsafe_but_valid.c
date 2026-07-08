int main()
{

int counter;
int total;
int value;

counter = 0;
total = 0;
value = 1;


/*
Large amount of normal looking computation
*/

total = total + 10;
total = total + 20;
total = total + 30;


print(total);



/*
The dangerous part

counter never changes.

The loop condition always remains true.

*/


while(counter < 100)
{

value = value + 1;

total = total + value;

print(value);


/*
Missing:

counter = counter + 1;

*/


}



return 0;

}