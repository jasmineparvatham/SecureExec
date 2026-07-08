int main() {
    int ptr;
    ptr = malloc(5);
    ptr[0] = 10;
    ptr[1] = 20;
    print(ptr[0] + ptr[1]);
    free(ptr);
    return 0;
}
