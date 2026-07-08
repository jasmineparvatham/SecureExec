int main() {
    int ptr;
    ptr = malloc(10);
    free(ptr);
    free(ptr); // Double free
    return 0;
}
