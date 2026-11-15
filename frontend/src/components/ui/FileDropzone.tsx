import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, X } from 'lucide-react';

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  acceptedExtensions?: string[];
  maxFiles?: number;
  maxSizeBytes?: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFilesSelected,
  acceptedExtensions = ['.pdf', '.docx'],
  maxFiles = 20,
  maxSizeBytes = 5 * 1024 * 1024, // 5MB
  multiple = true,
  disabled = false,
  className = '',
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndFilterFiles = (incomingFiles: FileList | File[]): File[] => {
    setErrorMsg(null);
    const valid: File[] = [];
    const filesArray = Array.from(incomingFiles);

    for (const file of filesArray) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedExtensions.includes(ext)) {
        setErrorMsg(`Invalid file type for "${file.name}". Accepted: ${acceptedExtensions.join(', ')}`);
        continue;
      }
      if (file.size > maxSizeBytes) {
        setErrorMsg(`"${file.name}" exceeds the maximum allowed size of 5MB`);
        continue;
      }
      valid.push(file);
    }

    if (valid.length > maxFiles) {
      setErrorMsg(`Maximum ${maxFiles} files can be uploaded in a single batch`);
      return valid.slice(0, maxFiles);
    }

    return valid;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const validated = validateAndFilterFiles(e.dataTransfer.files);
      if (validated.length > 0) {
        const nextFiles = multiple ? [...selectedFiles, ...validated] : validated;
        setSelectedFiles(nextFiles);
        onFilesSelected(nextFiles);
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const validated = validateAndFilterFiles(e.target.files);
      if (validated.length > 0) {
        const nextFiles = multiple ? [...selectedFiles, ...validated] : validated;
        setSelectedFiles(nextFiles);
        onFilesSelected(nextFiles);
      }
      // Reset input value so same files can be re-selected if removed
      e.target.value = '';
    }
  };

  const removeFile = (index: number) => {
    const updated = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updated);
    onFilesSelected(updated);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-indigo-500 bg-indigo-50/50 scale-[0.99]'
            : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50/50 bg-white'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple={multiple}
          accept={acceptedExtensions.join(',')}
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
        />
        <div className="flex flex-col items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-medium text-slate-800">
            <span className="text-indigo-600 hover:underline">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Supported formats: {acceptedExtensions.join(', ').toUpperCase()} (Up to 5MB each)
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 text-xs bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
          {errorMsg}
        </div>
      )}

      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
            <span>Queued Files ({selectedFiles.length})</span>
            <button
              type="button"
              onClick={() => {
                setSelectedFiles([]);
                onFilesSelected([]);
              }}
              className="text-rose-600 hover:underline"
            >
              Clear all
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
            {selectedFiles.map((file, idx) => (
              <div
                key={`${file.name}-${idx}`}
                className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                  <span className="truncate font-medium text-slate-700">{file.name}</span>
                  <span className="text-slate-400">({(file.size / 1024).toFixed(0)} KB)</span>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="text-slate-400 hover:text-rose-600 p-1"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
