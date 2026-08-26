# Portfolio Case Study: 3D QR Nameplate Generator

## Problem

Personalized 3D printed products often need a repeatable way to turn customer text and QR content into slicer-ready files.

## Solution

This app lets an operator type a name and QR content, preview the result in the browser, and generate a multicolor `.3mf` file with separated base/text/QR parts.

## Technical highlights

- FastAPI route returns a generated model file directly.
- QR content becomes actual raised geometry instead of a fragile SVG import.
- OpenSCAD handles parametric base/text generation.
- `trimesh` validates and reads temporary STL files before packaging.
- The `.3mf` is assembled manually as a ZIP-based 3D manufacturing package.

## Recruiter signal

It shows practical product engineering: user-facing workflow, file generation, geometry constraints, external tool integration, and clear setup docs.
