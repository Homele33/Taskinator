import React, { useState, useEffect } from "react";
import { Subtask } from "./task";

export interface SubtaskFormData {
  title: string;
  description: string;
  parentId: string;
}

interface SubtaskFormProps {
  subtask?: Subtask;
  parentId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (subtaskData: SubtaskFormData) => Promise<void>;
}

const SubtaskForm: React.FC<SubtaskFormProps> = ({
  subtask,
  parentId,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const defaultData = {
    title: "",
    description: "",
    parentId: parentId,
  };
  const [formData, setFormData] = useState<SubtaskFormData>(defaultData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (subtask) {
      setFormData({
        title: subtask.title,
        description: subtask.description || "",
        parentId: subtask.parentId,
      });
    }
  }, [subtask, parentId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await onSubmit(formData);
      setFormData(defaultData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save subtask");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative rounded-lg shadow-xl w-96 p-6 bg-base-100">
        <h3 className="text-lg font-semibold mb-4">
          {subtask ? "Edit Subtask" : "Add Subtask"}
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input
                type="text"
                name="title"
                defaultValue={subtask?.title}
                className="w-full border rounded-md px-3 py-2 bg-base-200"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Description
              </label>
              <textarea
                name="description"
                defaultValue={subtask?.description}
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full border rounded-md px-3 py-2 bg-base-200"
                rows={3}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              {subtask ? "Save Changes" : "Add Subtask"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SubtaskForm;
