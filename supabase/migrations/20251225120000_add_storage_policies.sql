-- Storage policies for user-documents bucket
-- Allow users to upload their own documents
CREATE POLICY "Users can upload their own documents"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'user-documents' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to view/download their own documents
CREATE POLICY "Users can view their own documents"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'user-documents' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to update their own documents
CREATE POLICY "Users can update their own documents"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'user-documents' 
  AND (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
  bucket_id = 'user-documents' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to delete their own documents
CREATE POLICY "Users can delete their own documents"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'user-documents' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow service role (backend) to manage all documents
CREATE POLICY "Service role can manage all documents"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'user-documents')
WITH CHECK (bucket_id = 'user-documents');
