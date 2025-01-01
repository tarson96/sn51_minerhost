#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>

// Mock NVML types and constants
typedef void* nvmlDevice_t;
typedef enum nvmlReturn_enum {
    NVML_SUCCESS = 0
} nvmlReturn_t;

// Mock implementation of nvmlDeviceGetName
nvmlReturn_t nvmlDeviceGetName(nvmlDevice_t device, char *name, unsigned int length) {
    // Simply return the desired GPU name
    strncpy(name, "NVIDIA H100 80GB HBM3", length);
    return NVML_SUCCESS;
}