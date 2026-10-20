# Microsoft runtime distribution review

Reviewed 20 October 2026. Status: pending; this record does not clear redistribution.

The retained local candidate contains fourteen Microsoft runtime DLLs across Python,
Qt, NumPy and Shapely locations. Their signatures all validate, but the files span
several runtime versions. Package-relative paths, versions, SHA-256 values and signers
are recorded in `evidence/msvc-runtime-inventory.json`. That inventory describes its
named candidate, not future build outputs. Authenticity does not establish permission.

## Reviewed official terms

The [Visual C++ V14 runtime terms](https://visualstudio.microsoft.com/license-terms/vs2026-ga-visualcpp-v14-redist-runtime/)
permit installation and use, while section 4 restricts distribution and transfer.
This end-user licence alone does not establish Luma's redistribution grant. The
linked full DOCX was read through Microsoft's Office viewer after direct retrieval
returned HTTP 403. It identifies EULA Cpp_v14_ENU.1033, updated 1 October 2025.

The [Visual Studio 2026 Build Tools terms](https://visualstudio.microsoft.com/license-terms/vs2026-ga-diagnostic-buildtools/)
include a limited exception for building required third-party open-source C++
dependencies without a Visual Studio licence. That exception is not a general
application development or runtime redistribution grant. The reviewed standalone
tools agreement has no Distributable Code grant comparable to Community section 8.

The [Visual Studio 2026 Community terms](https://visualstudio.microsoft.com/license-terms/vs2026-ga-community/)
permit individual developers to develop their own applications, including for sale.
Section 8 grants distribution of covered object code subject to conditions, including
significant application functionality, protective downstream terms, indemnity and
restrictions on excluded licensing. This is a possible route requiring an established
valid licence and a review of how those conditions apply to the distribution.
No Visual Studio agreement has been accepted or product installed by this review.

The [2026 REDIST list](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution)
requires valid licensing and applicable terms. It covers specified runtime packages
and unmodified files within designated Visual Studio redistribution directories,
excluding debug files. Filename similarity alone does not map every bundled DLL to
that coverage. The [C++ distribution guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170)
also requires an applicable Visual Studio licence.

## Before clearing the gate

- Establish the applicable licence grant and record the covered distribution terms.
- Map the actual files from each dependency/build environment to permitted runtime
  distribution coverage; reconcile mixed versions without speculative replacement.
- Review downstream terms and the boundary between Microsoft runtime components and
  Luma's AGPL-covered source. Preserve the applicable notices without relicensing
  Microsoft's code as Luma code.
- Re-inventory the final build and retain evidence for those exact artifacts.

A successful hosted build, a valid signature, or an open-source build exception
alone cannot clear this gate. The existing local installer and portable archive have
not been rebuilt or approved for public distribution by this documentation update.

## Python Windows build conditions

The official Python 3.13.16 build package's complete LICENSE.txt was retained and its original bytes preserved by the notice-copy helper. Its Windows-specific section describes Microsoft code embedded in the interpreter's EXE/DLL/PYD files and permits redistribution of the Windows interpreter subject to stated conditions. These include preserving notices, avoiding misleading Microsoft branding, the Microsoft-platform restriction and protective downstream terms, with the restrictions scoped to Microsoft's code. This is relevant component-specific evidence; it does not automatically establish coverage for separate runtime DLLs collected from Qt, scientific wheels or a host system directory. Map the actual final component set and downstream terms before clearing the Microsoft gate. The full Python licence remains bundled separately; no additional restrictions are asserted over Luma's own source.
