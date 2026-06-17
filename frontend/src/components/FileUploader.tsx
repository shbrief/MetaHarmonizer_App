import React, { useCallback, useState } from 'react';
import { Upload } from 'lucide-react';

interface Props {
  onFileSelected: (file: File) => void;
  accept?: string;
  disabled?: boolean;
}

export default function FileUploader({ onFileSelected, accept = '.csv,.tsv,.txt', disabled }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files?.[0];
      if (file) {
        setFileName(file.name);
        onFileSelected(file);
      }
    },
    [onFileSelected],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setFileName(file.name);
        onFileSelected(file);
      }
    },
    [onFileSelected],
  );

  return (
    <label
      className={`flex flex-col items-center justify-center w-full h-52 border-2 border-dashed rounded-2xl cursor-pointer transition
        ${dragActive ? 'border-primary-500 bg-primary-50' : 'border-slate-300 bg-white hover:border-primary-300 hover:bg-slate-50'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
    >
      <span className={`grid h-14 w-14 place-items-center rounded-2xl transition ${dragActive ? 'bg-primary-100 text-primary-600' : 'bg-slate-100 text-slate-400'}`}>
        <Upload className="h-7 w-7" />
      </span>
      {fileName ? (
        <p className="mt-3 text-sm font-semibold text-primary-700">{fileName}</p>
      ) : (
        <>
          <p className="mt-3 text-sm text-slate-600">
            <span className="font-semibold text-primary-600">Click to upload</span> or drag and drop
          </p>
          <p className="mt-1 text-xs text-slate-400">CSV, TSV, or TXT · up to 50&nbsp;MB</p>
        </>
      )}
      <input
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
      />
    </label>
  );
}
