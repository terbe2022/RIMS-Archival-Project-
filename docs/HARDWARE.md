# Current execution hardware

Observed October 13, 2026 from a user-supplied server inventory. This is a sanitized capacity summary, not the raw diagnostic transcript or a throughput benchmark. It omits host/account identifiers, private paths, process IDs, volume names and live workload details.

## Allocated server resources

| Resource | Observed specification |
| --- | --- |
| Deployment | KVM virtual machine; GPU pass-through |
| CPU | Four guest-visible logical CPUs; Intel Xeon Ice Lake processor identification |
| Memory | 62 GiB guest-visible RAM; 4 GiB swap |
| GPU | One NVIDIA L4, Ada Lovelace architecture |
| GPU memory | 23,034 MiB reported total, approximately 22.5 GiB |
| Compute capability | 8.9 |
| Power limit | 72 W reported configured/max limit |
| PCIe capability | Reported maximum generation 4, width x16; negotiated link not measured |
| ECC | Enabled |
| MIG | Reported not applicable |
| GPU clocks | Reported maximum SM 2,040 MHz; memory 6,251 MHz; not measured sustained clocks |
| Working-data filesystem | Approximately 652 GiB capacity reported by df -h |
| OS | Red Hat Enterprise Linux 9.8; x86_64 |

The CPU/socket layout and cache values are guest-exposed virtualization information, not proof of the physical host's socket count or dedicated CPU allocation. Virtual-disk rotational flags do not establish physical HDD/SSD media. Storage capacity is filesystem-level, not a per-project reservation. Available RAM, disk and VRAM vary with other workloads and are intentionally not published here as promised capacity.

## Observed software, not a lockfile

| Component | Reported version |
| --- | --- |
| NVIDIA driver | 610.57.04 |
| Default python3 | 3.9.25 |
| PyTorch | 2.8.0 |
| Transformers | 4.57.6 |
| vLLM | 0.11.0 |
| torchvision / torchaudio | 0.23.0 / 2.8.0 |
| xformers | 0.0.32.post1 |
| xgrammar | 0.1.25 |
| sentence-transformers | 5.1.2 |
| scikit-learn | 1.6.1 |

Package versions were reported by pip for the inspected default Python environment. Another Python environment exposed different packages, and the active inference process used a separate Python 3.11 environment. The inventory therefore does **not** prove these versions are the running inference service's dependencies. Record the exact interpreter and package versions for every evaluation.

The supplied output ends partway through environment inspection. CUDA toolkit/runtime version, active model/configuration, container availability and outbound connectivity are not established by this transcript. A driver version is not a CUDA toolkit version. No environment changes or performance tests were performed to create this summary.

## Implications for evaluation

Start with a small model and a bounded synthetic smoke run. Check actual free memory privately immediately before allocating a model; don't stop another service to reclaim GPU memory. Four virtual CPUs may limit extraction/preprocessing independently of GPU inference; measure those stages separately. Model weights, KV cache, input/output lengths, concurrency and serving overhead all affect fit—GPU size alone does not establish a supported model size.

For comparisons record hardware, exact execution environment, model revision/quantization, context/chunk settings, output budget, warmup, concurrency and repetitions. Do not carry throughput from the legislation case study into this pipeline without measurement. Colab's allocated GPU may differ or be unavailable; record its actual hardware rather than assuming equivalence.

See [project state](PROJECT-GUIDE.md) and [evaluation methodology](EVALUATION.md). The server code deployment is verified separately; model execution and quality remain separate evidence requirements.
