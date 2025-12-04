#include <iostream>
#include <vector>
#include <algorithm>

void printArray(const std::vector<int>& arr) {
    for (int num : arr) {
        std::cout << num << " ";
    }
    std::cout << std::endl;
}

int main() {
    std::vector<int> arr = {10, 7, 8, 9, 1, 5};

    std::cout << "Original array: ";
    printArray(arr);

    std::sort(arr.begin(), arr.end());

    std::cout << "Sorted array: ";
    printArray(arr);

    return 0;
}
