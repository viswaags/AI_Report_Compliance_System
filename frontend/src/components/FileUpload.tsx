import { useCallback, useState } from 'react';
import { Upload, X, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface FileUploadProps {
  accept?: string;
  maxSize?: number;
  onFileSelect: (file: File) => void;
  onFileRemove?: () => void;
  selectedFile?: File | null;
  className?: string;
  disabled?: boolean;
}

export function FileUpload({
  accept = '.pdf,.doc,.docx',
  maxSize = 10 * 1024 * 1024,
  onFileSelect,
  onFileRemove,
  selectedFile,
  className,
  disabled = false,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const validateFile = useCallback(
    (file: File): string | null => {
      if (maxSize && file.size > maxSize) {
        return `File size exceeds ${formatFileSize(maxSize)} limit`;
      }
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (accept && !accept.includes(ext)) {
        return `File type not accepted. Please upload ${accept.replace(/\./g, ' ').trim()} files`;
      }
      return null;
    },
    [accept, maxSize]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      setError(null);

      const file = e.dataTransfer.files[0];
      if (file) {
        const validationError = validateFile(file);
        if (validationError) {
          setError(validationError);
        } else {
          onFileSelect(file);
        }
      }
    },
    [validateFile, onFileSelect]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setError(null);
      const file = e.target.files?.[0];
      if (file) {
        const validationError = validateFile(file);
        if (validationError) {
          setError(validationError);
        } else {
          onFileSelect(file);
        }
      }
    },
    [validateFile, onFileSelect]
  );

  return (
    <div className={cn('w-full', className)}>
      {selectedFile ? (
        <div className="flex items-center gap-4 rounded-lg border border-border bg-muted/30 p-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-foreground">
              {selectedFile.name}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(selectedFile.size)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-500" />
            {onFileRemove && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onFileRemove}
                disabled={disabled}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      ) : (
        <label
          className={cn(
            'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50 hover:bg-muted/30',
            disabled && 'opacity-50 cursor-not-allowed',
            error && 'border-red-500 bg-red-50'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            className="hidden"
            accept={accept}
            onChange={handleFileSelect}
            disabled={disabled}
          />
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="rounded-full bg-primary/10 p-3">
              <Upload className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                {dragActive ? 'Drop file here' : 'Drag and drop file here'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                or click to browse from your computer
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Accepted formats: {accept} (max {formatFileSize(maxSize)})
            </p>
          </div>
        </label>
      )}

      {error && (
        <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
