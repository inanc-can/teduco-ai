import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { config } from '@/lib/config'

// Query keys
export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: () => [...documentKeys.lists()] as const,
}

/**
 * Fetch all documents for the current user
 */
export function useDocuments() {
  return useQuery({
    queryKey: documentKeys.list(),
    queryFn: () => apiClient.getDocuments(),
    retry: 1, // Only retry once for documents
    staleTime: 30000, // 30 seconds
    // Don't throw error, just return empty array if backend is down
    placeholderData: [],
  })
}

/**
 * Upload a document with file validation
 */
export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, docType }: { file: File; docType?: string }) => {
      // Validate file size
      if (file.size > config.upload.maxFileSize) {
        throw new Error(
          `File size exceeds maximum allowed size of ${
            config.upload.maxFileSize / 1024 / 1024
          }MB`
        )
      }

      // Validate file type
      if (!config.upload.allowedFileTypes.includes(file.type as any)) {
        throw new Error(
          `File type ${file.type} is not supported. Allowed types: PDF, DOC, DOCX, TXT, JPG, PNG`
        )
      }

      return apiClient.uploadDocument(file, docType)
    },
    onMutate: ({ file }) => {
      // Show upload started toast
      toast.loading(`Uploading ${file.name}...`, {
        id: `upload-${file.name}`,
      })
    },
    onSuccess: (data, { file }) => {
      // Dismiss loading toast
      toast.dismiss(`upload-${file.name}`)
      
      // Show success toast
      toast.success(`${file.name} uploaded successfully`)
      
      // Invalidate documents list to refetch
      queryClient.invalidateQueries({ queryKey: documentKeys.list() })
    },
    onError: (error: Error, { file }) => {
      // Dismiss loading toast
      toast.dismiss(`upload-${file.name}`)
      
      // Show error toast
      toast.error(`Failed to upload ${file.name}: ${error.message}`)
    },
  })
}

/**
 * Delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => apiClient.deleteDocument(documentId),
    onMutate: () => {
      toast.loading('Deleting document...', { id: 'delete-document' })
    },
    onSuccess: () => {
      toast.dismiss('delete-document')
      toast.success('Document deleted successfully')
      
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: documentKeys.list() })
    },
    onError: (error: Error) => {
      toast.dismiss('delete-document')
      toast.error(`Failed to delete document: ${error.message}`)
    },
  })
}

/**
 * Upload multiple documents
 */
export function useUploadMultipleDocuments() {
  const queryClient = useQueryClient()
  const uploadDocument = useUploadDocument()

  return useMutation({
    mutationFn: async (files: File[]) => {
      const results = await Promise.allSettled(
        files.map((file) => uploadDocument.mutateAsync({ file }))
      )

      const successful = results.filter((r) => r.status === 'fulfilled').length
      const failed = results.filter((r) => r.status === 'rejected').length

      return { successful, failed, total: files.length }
    },
    onSuccess: ({ successful, failed, total }) => {
      if (failed === 0) {
        toast.success(`All ${total} documents uploaded successfully`)
      } else if (successful > 0) {
        toast.warning(
          `${successful} documents uploaded, ${failed} failed`
        )
      } else {
        toast.error(`Failed to upload all ${total} documents`)
      }

      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: documentKeys.list() })
    },
    onError: (error: Error) => {
      toast.error(`Upload failed: ${error.message}`)
    },
  })
}
