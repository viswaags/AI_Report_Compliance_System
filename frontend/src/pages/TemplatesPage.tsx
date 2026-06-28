import { useState } from 'react';
import { CheckCircle, FileStack, FileText, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { FileUpload } from '@/components/FileUpload';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';
import {
  useActiveTemplate,
  useTemplates,
  useUploadTemplate,
} from '@/hooks/useTemplates';

type Template = {
  id?: number;
  template_id?: number;
  version: string;
  drive_url?: string | null;
  template_schema?: unknown;
  schema_json?: unknown;
};

function idOf(template: Template) {
  return template.id ?? template.template_id ?? template.version;
}

function schemaOf(template?: Template | null) {
  return template?.template_schema ?? template?.schema_json;
}

function renderSchema(template?: Template | null) {
  const schema = schemaOf(template);
  if (!schema) return 'No schema returned.';
  if (typeof schema === 'string') return schema;
  return JSON.stringify(schema, null, 2);
}

export function TemplatesPage() {
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadVersion, setUploadVersion] = useState('');
  const [schemaTemplate, setSchemaTemplate] = useState<Template | null>(null);
  const { user } = useAuth();

  const templatesQuery = useTemplates();
  const activeTemplateQuery = useActiveTemplate();
  const uploadTemplate = useUploadTemplate();
  const isAdmin = user?.role === 'ADMIN';

  const templates = Array.isArray(templatesQuery.data) ? (templatesQuery.data as Template[]) : [];
  const activeTemplate = activeTemplateQuery.data as Template | undefined;

  const handleUploadTemplate = () => {
    if (!uploadFile || !uploadVersion.trim()) return;

    uploadTemplate.mutate(
      { version: uploadVersion.trim(), file: uploadFile },
      {
        onSuccess: () => {
          setUploadFile(null);
          setUploadVersion('');
          toast.success('Template uploaded successfully.');
        },
        onError: () => {
          toast.error('Unable to upload template.');
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Templates</h1>
          <p className="text-muted-foreground">Manage report templates for validation</p>
        </div>
      </div>

      <Tabs defaultValue="current" className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="current">
            <FileStack className="mr-2 h-4 w-4" />
            Current Template
          </TabsTrigger>
          {isAdmin && (
            <TabsTrigger value="upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload Template
            </TabsTrigger>
          )}
          {isAdmin && <TabsTrigger value="history">Template History</TabsTrigger>}
        </TabsList>

        <TabsContent value="current">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Current Template
                {activeTemplate && (
                  <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Backend Current
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>Determined by the backend current template endpoint</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {activeTemplateQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading current template...</p>
              ) : activeTemplateQuery.isError || !activeTemplate ? (
                <p className="text-sm text-muted-foreground">No current template returned.</p>
              ) : (
                <>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-lg border border-border p-4">
                      <p className="text-sm text-muted-foreground">Current Version</p>
                      <p className="text-lg font-medium">{activeTemplate.version}</p>
                    </div>
                    <div className="rounded-lg border border-border p-4">
                      <p className="text-sm text-muted-foreground">Current Status</p>
                      <Badge className="mt-2 bg-emerald-100 text-emerald-800 hover:bg-emerald-100">
                        Active
                      </Badge>
                    </div>
                    <div className="rounded-lg border border-border p-4">
                      <p className="text-sm text-muted-foreground">View Template</p>
                      {activeTemplate.drive_url ? (
                        <Button asChild variant="outline" size="sm" className="mt-2">
                          <a href={activeTemplate.drive_url} target="_blank" rel="noreferrer">
                            Open Template
                          </a>
                        </Button>
                      ) : (
                        <p className="mt-2 text-sm text-muted-foreground">Preview unavailable</p>
                      )}
                    </div>
                  </div>

                  {isAdmin && (
                    <div>
                      <h4 className="mb-3 font-medium">Template Schema</h4>
                      <pre className="max-h-96 overflow-auto rounded-lg border border-border bg-muted/30 p-3 text-xs">
                        {renderSchema(activeTemplate)}
                      </pre>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {isAdmin && (
        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Upload New Template</CardTitle>
              <CardDescription>Upload a PDF or DOCX template file with a version</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="upload-version">Template Version</Label>
                  <Input
                    id="upload-version"
                    value={uploadVersion}
                    onChange={(event) => setUploadVersion(event.target.value)}
                    placeholder="v1.0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Template File</Label>
                  <FileUpload
                    selectedFile={uploadFile}
                    onFileSelect={setUploadFile}
                    onFileRemove={() => setUploadFile(null)}
                    accept=".docx,.pdf"
                    disabled={uploadTemplate.isPending}
                  />
                </div>
              </div>

              {uploadTemplate.isError && (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to upload template.
                </p>
              )}

              <div className="flex justify-end">
                <Button
                  disabled={!uploadFile || !uploadVersion.trim() || uploadTemplate.isPending}
                  onClick={handleUploadTemplate}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {uploadTemplate.isPending ? 'Uploading...' : 'Upload Template'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        )}

        {isAdmin && (
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Template History</CardTitle>
              <CardDescription>Templates returned by the backend</CardDescription>
            </CardHeader>
            <CardContent>
              {templatesQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading templates...</p>
              ) : templatesQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to load templates.
                </p>
              ) : templates.length === 0 ? (
                <p className="text-sm text-muted-foreground">No templates returned.</p>
              ) : (
                <div className="space-y-4">
                  {templates.map((template) => (
                    <div key={idOf(template)} className="flex items-center justify-between rounded-lg border border-border p-4">
                      <div className="flex items-center gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                          <FileText className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">Version {template.version}</p>
                          {template.id && (
                            <p className="text-xs text-muted-foreground">Template ID {template.id}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {activeTemplate?.version === template.version && (
                          <Badge className="bg-emerald-100 text-emerald-800">Current</Badge>
                        )}
                        <Button size="sm" variant="outline" onClick={() => setSchemaTemplate(template)}>
                          View Schema
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        )}
      </Tabs>

      {isAdmin && (
        <Dialog open={!!schemaTemplate} onOpenChange={(open) => !open && setSchemaTemplate(null)}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Template Schema</DialogTitle>
              <DialogDescription>
                {schemaTemplate ? `Version ${schemaTemplate.version}` : undefined}
              </DialogDescription>
            </DialogHeader>
            <pre className="max-h-[60vh] overflow-auto rounded-lg border border-border bg-muted/30 p-3 text-xs">
              {renderSchema(schemaTemplate)}
            </pre>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

export default TemplatesPage;
