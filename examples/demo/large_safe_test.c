int main()
{

int total = 0;
int i = 0;

print(1);
print(2);
print(3);


total = 10;
total = total + 20;
total = total + 30;
total = total - 5;

print(total);





i = 0;

while(i < 10)
{

print(i);

i = i + 1;

}



i = 0;

while(i < 50)
{

total = total + i;

i = i + 1;

}



print(total);





if(total > 100)
{

print(total);

}

else
{

print(0);

}




total = add(total,10);

total = add(total,20);

total = add(total,30);

print(total);





int numbers[20];


numbers[0] = 10;
numbers[1] = 20;
numbers[2] = 30;
numbers[3] = 40;
numbers[4] = 50;


print(numbers[0]);
print(numbers[1]);
print(numbers[2]);
print(numbers[3]);
print(numbers[4]);



i = 0;

while(i < 20)
{

numbers[i] = i;

i = i + 1;

}


i = 0;

while(i < 20)
{

print(numbers[i]);

i = i + 1;

}





int sum;

sum = 0;

i = 0;

while(i < 100)
{

sum = sum + i;

i = i + 1;

}


print(sum);





int ptr;

ptr = malloc(10);


ptr[0] = 100;
ptr[1] = 200;
ptr[2] = 300;


print(ptr[0]);
print(ptr[1]);
print(ptr[2]);


free(ptr);




total = 0;


i = 0;

while(i < 200)
{

total = total + i;

i = i + 1;

}


print(total);



return 0;

}



int add(int a,int b)
{

int result;

result = a+b;

return result;

}