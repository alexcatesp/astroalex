# Shared Types and Schemas

This directory contains type definitions and schemas shared between the frontend and backend.

## Contents

- `types.ts` - TypeScript type definitions

## Usage

### Frontend (TypeScript)

```typescript
import { Project, FileMetadata } from '@/shared/types';
```

### Backend (Python)

The Python backend should define equivalent Pydantic models that match these TypeScript types to ensure type safety across the full stack.

## Keeping Types in Sync

When modifying types:
1. Update the TypeScript definitions in `types.ts`
2. Update the corresponding Pydantic models in the backend
3. Ensure API contracts remain compatible
