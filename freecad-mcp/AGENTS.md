# FreeCAD MCP

- Preserve the original FreeCAD source tree and existing models.
- MCP stdout is protocol only; log to stderr.
- Run all CAD/GUI operations on the Qt main thread.
- Do not introduce arbitrary code execution endpoints.
- Keep paths restricted to modelos and credentials under .runtime.
- Run `.venv/Scripts/python.exe -m pytest` for unit tests.
- Integration tests require a real FreeCAD bridge; explicitly set FREECAD_INTEGRATION=1.
- No simulated CAD success: report actual runtime evidence.
