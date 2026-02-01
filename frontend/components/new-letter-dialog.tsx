"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useCreateLetter } from "@/hooks/api/use-letters"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface NewLetterDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function NewLetterDialog({ open, onOpenChange }: NewLetterDialogProps) {
  const [title, setTitle] = useState("")
  const router = useRouter()
  const createLetter = useCreateLetter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!title.trim()) {
      return
    }

    try {
      const newLetter = await createLetter.mutateAsync({
        title: title.trim(),
        content: "",
        status: "draft",
      })

      // Close dialog and navigate to the new letter
      onOpenChange(false)
      setTitle("")
      router.push(`/edit/${newLetter.id}`)
    } catch (error) {
      // Error handling is done in the mutation hook
      console.error("Failed to create letter:", error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Letter</DialogTitle>
            <DialogDescription>
              Give your application letter a title. You can start writing immediately.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                placeholder="e.g., TUM Informatics Application"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!title.trim() || createLetter.isPending}>
              {createLetter.isPending ? "Creating..." : "Create Letter"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
