# FREAK 3D Math & GPU Bindings Plan

## 1. Objective
Implement a high-performance 3D math library and low-level GPU bindings for the FREAK language, enabling the development of 3D applications, games, and hardware-accelerated UI. The implementation must strictly adhere to FREAK's Anime/Visual Novel aesthetic (e.g., `pilot`, `task`, `shape`, `trust me` blocks).

## 2. Phase 1: 3D Math Foundation (`std/math3d.fk`)
The math library will provide the core types required for 3D graphics: Vectors and Matrices.

### 2.1 Shapes & Doctrines
We will define `Vector2`, `Vector3`, `Vector4`, and `Matrix4x4` as `shape`s. 
Operator overloading will be implemented using `doctrine`s to allow ergonomic math operations.

```freak
shape Vector3 {
    pilot x: float32
    pilot y: float32
    pilot z: float32
}

doctrine Add for Vector3 {
    task add(pilot self, pilot other: Vector3) -> Vector3 {
        give back Vector3 { 
            x: self.x + other.x, 
            y: self.y + other.y, 
            z: self.z + other.z 
        }
    }
}
```

### 2.2 Core Math Tasks
Implement essential graphics math operations:
- `dot(a, b)`
- `cross(a, b)`
- `normalize(v)`
- `magnitude(v)`
- Matrix multiplication, translation, rotation, and scaling `task`s.

### 2.3 SIMD Optimization
To ensure performance, critical paths like Matrix-Matrix multiplication and Vector operations will use `trust me` blocks with `direct_order` to emit optimized LLVM IR or map to C SIMD intrinsics (as outlined in `freak-full-bible.md` under `math::simd`).

## 3. Phase 2: GPU Bindings Architecture (`packages/gpu/`)
FREAK will bind to a modern graphics API via C FFI. We will target **WebGPU (via wgpu-native)** or **Vulkan** as the primary backend due to their cross-platform C APIs.

### 3.1 C FFI Wrappers
Since FREAK compiles to C/LLVM IR, we can interface directly with C headers. We will define opaque handles as pointer `shape`s in FREAK.

```freak
shape GpuDevice {
    pilot handle: ptr // Opaque pointer to wgpuDevice or VkDevice
}

shape GpuBuffer {
    pilot handle: ptr
}
```

### 3.2 The GPU API
We will create a higher-level, FREAK-idiomatic API wrapping the raw C calls. 

```freak
task request_device(pilot adapter: GpuAdapter) -> GpuDevice {
    trust me on my honor as humanity {
        // C FFI call to wgpuAdapterRequestDevice or vkCreateDevice
        // Handle "knowing this will hurt" for initialization failures.
    }
}

task create_buffer(pilot device: GpuDevice, pilot size: int32) -> GpuBuffer {
    // Allocation logic
}
```

## 4. Phase 3: Shaders and Pipelines
- **Shader Language:** Initially, developers will write shaders in WGSL (for WebGPU) or GLSL/HLSL (compiled to SPIR-V for Vulkan) and load them as strings or byte arrays (`bytes`) into FREAK.
- **Pipelines:** Provide `shape`s for `RenderPipelineDescriptor` to configure the GPU state (depth testing, blending, etc.).

## 5. Aesthetic & Lore Integration
- **Variables/Keywords:** Use `pilot`, `task`, `give back`, `shape`.
- **Error Handling:** GPU device loss or memory allocation failures must trigger "Cockpit Failure" or "Pilot sync ratio dropped" styled diagnostics. Use `knowing this will hurt` for fallible operations.
- **Unsafe Code:** All FFI calls to the C GPU API must be wrapped in `trust me on my honor as humanity` blocks.

## 6. Execution Steps
1. Create `std/math3d.fk` and implement `Vector2/3/4` and `Matrix4x4` with tests.
2. Add compiler support for floating-point SIMD intrinsics if missing.
3. Choose the C GPU library (e.g., download `wgpu-native` binaries).
4. Create the FFI bindings in `packages/gpu/bindings.fk`.
5. Write a `hello_triangle.fk` test demonstrating window creation (integrating with `freak-ui`), device initialization, buffer creation, and a basic render pass.