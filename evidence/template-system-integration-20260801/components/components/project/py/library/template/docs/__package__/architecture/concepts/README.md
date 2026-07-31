---
name: architecture-concepts
doc_type: index
description: Index of the architecture concept slices for [[[ project_title_lower ]]]. Use when you need one focused runtime slice at a time.
---

# Concepts

## Overview

Concept docs should describe durable product slices. The baseline
includes only the public-boundary concept because no product runtime exists yet.

## Files

- [public-boundary-and-errors.md](public-boundary-and-errors.md)
  Explains the public output and error boundary.
  Use it to understand why raw internals should not cross the package boundary.
