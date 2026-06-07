# Concept Graph Frontend Integration Guide

This guide provides the necessary details for integrating the **Concept Graphs Module** into the Next.js frontend. This feature identifies key entities and their semantic relationships within a document.

---

## 1. API Specification

- **Endpoint**: `POST /insight/v2/concept-graph/`
- **Content-Type**: `multipart/form-data`

### Request Parameters:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `file` | `File (PDF)` | Yes | The PDF document to analyze. |
| `use_api` | `boolean` | No | `true` to use Gemini API (fast/accurate), `false` to use local Mistral (default). |
| `max_concepts` | `integer` | No | Limit the number of nodes in the graph (default: 10). |

---

## 2. Response Structure

The API returns a JSON object containing nodes and links, optimized for force-directed graph libraries.

```json
{
  "pdf_name": "filename.pdf",
  "engine": "Gemini API",
  "graph": {
    "nodes": [
      { "id": "concept_1", "label": "Artificial Intelligence", "type": "topic" }
    ],
    "links": [
      { "source": "concept_1", "target": "concept_2", "relation": "encompasses" }
    ]
  }
}
```

---

## 3. Implementation in Next.js

Since graph libraries rely on the `window` and `document` objects, you **must** use dynamic imports with `ssr: false` to avoid errors during build or hydration.

### Step 1: Install Dependencies
```bash
npm install react-force-graph
```

### Step 2: Create the Graph Component
Create a file at `components/ConceptGraphCustom.js`:

```jsx
import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamic import to disable SSR for this heavy canvas/svg library
const ForceGraph2D = dynamic(() => import('react-force-graph').then(mod => mod.ForceGraph2D), {
  ssr: false,
  loading: () => <div className="h-[500px] flex items-center justify-center bg-gray-50">Loading Graph Engine...</div>
});

export default function ConceptGraph({ data }) {
  if (!data || !data.nodes) return null;

  return (
    <div className="rounded-xl border border-gray-200 overflow-hidden bg-white shadow-sm">
      <ForceGraph2D
        graphData={data}
        nodeLabel="label"
        nodeAutoColorBy="type"
        linkColor={() => '#94a3b8'}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.2}
        height={500}
        // Custom styling for nodes
        nodeCanvasObject={(node, ctx, globalScale) => {
          const label = node.label;
          const fontSize = 14 / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = node.color;
          ctx.beginPath(); 
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false); 
          ctx.fill();
          ctx.fillStyle = '#1e293b';
          ctx.fillText(label, node.x, node.y + 10);
        }}
      />
    </div>
  );
}
```

### Step 3: Use in your Page
```jsx
const [graphData, setGraphData] = useState(null);

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  const formData = new FormData();
  formData.append('file', file);
  formData.append('use_api', 'true'); // Optional toggle

  const response = await fetch('http://YOUR_BACKEND_URL/insight/v2/concept-graph/', {
    method: 'POST',
    body: formData,
  });

  const result = await response.json();
  setGraphData(result.graph);
};
```

---

## 4. Key Considerations
1.  **CORS**: Ensure the backend allows requests from your frontend domain.
2.  **State Management**: Store only the `graph` object from the response in your state.
3.  **Visualization**: The `react-force-graph` library is highly customizable. You can adjust link distance, charge strength, and colors to match your UI design.
