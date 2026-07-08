int main(){
    int arr;
    arr = malloc(5);
    arr[0] = 10;
    arr[1] = 20;
    print(arr[0] + arr[1]);
    free(arr);
    return 0;
}
