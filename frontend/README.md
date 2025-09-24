# Patient Document Management Frontend

A React TypeScript application for managing patient documents with AI-powered data extraction and chat functionality.

## Features

- **Document Upload**: Drag & drop interface for patient documents (images, PDFs, text files)
- **AI Data Extraction**: Automatic extraction of patient information using Google Gemini 2.5-pro
- **Form Validation**: Comprehensive form for patient data entry and validation
- **Patient Management**: List, edit, and delete patient records
- **AI Chat**: Intelligent chat interface to query patient data using RAG (Retrieval-Augmented Generation)
- **Responsive Design**: Modern UI built with Tailwind CSS

## Prerequisites

- Node.js 16 or higher
- npm or yarn package manager

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file (optional):
```bash
cp .env.example .env
```

4. Update environment variables if needed:
```
REACT_APP_API_URL=http://localhost:8000
```

## Development

Start the development server:
```bash
npm start
```

The application will be available at http://localhost:3000

## Build

Create a production build:
```bash
npm run build
```

## Available Scripts

- `npm start`: Start development server
- `npm run build`: Create production build
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App (not recommended)

## Components

### DocumentUpload
Drag & drop interface for uploading patient documents with support for:
- Images (JPEG, PNG)
- PDF files
- Text files

### PatientForm
Form component for entering and editing patient information:
- Name (required)
- Date of Birth (required)
- Diagnosis (optional)
- Prescription (optional)

### PatientList
Display and manage patient records with:
- Patient information display
- Edit functionality
- Delete functionality
- Responsive design

### ChatInterface
AI-powered chat interface with:
- Real-time messaging
- Context from patient database
- Source attribution
- Message history

## API Integration

The frontend communicates with the FastAPI backend through:
- Document processing endpoints
- Patient CRUD operations
- Chat functionality with RAG system

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Custom Components**: Consistent design system
- **Responsive Design**: Works on desktop and mobile devices
