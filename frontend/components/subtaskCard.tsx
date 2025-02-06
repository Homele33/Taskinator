import { Subtask } from "./task";
import { Pencil, Trash2 } from "lucide-react";

interface SubtaskCardProps {
  subtask: Subtask;
  level?: number;
  parentId: string;
  isDone: boolean;
  onRefresh: () => void;
}

const getCardStyles = (isDone: boolean) => {
  const className =
    "border-base-100 card hadow-lg hover:shadow-xl transition-shadow scale-90 opacity-90";
  if (!isDone) {
    return `${className}   border-l-4 bg-base-300 `;
  }
  return `${className} `;
};

export const SubtaskCard: React.FC<SubtaskCardProps> = ({
  subtask,
  level = 1,
  onRefresh,
  parentId,
}) => {
  const handleDeleteSubtask = async (id: string) => {
    const response = await fetch(
      `http://localhost:5000/api/${parentId}/${id}/delete_subtask`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to delete subtask");
    }
    onRefresh();
  };

  const handleEditSubtask = async (subtask: Subtask) => {
    throw new Error(`Function not implemented. subtask ${subtask.title}`);
  };

  return (
    <div className={`ml-${level * 12}`}>
      <div className={`${getCardStyles(subtask.isDone)}`}>
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold">{subtask.title}</h2>
            </div>

            <div className="flex">
              <ul tabIndex={0} className=" p-2 shadow">
                <li>
                  <div className="tooltip" data-tip="Edit subtask">
                    <button
                      onClick={() => handleEditSubtask(subtask)}
                      className="btn btn-ghost btn-md text-yellow-400 p-2">
                      <Pencil /> {/* Edit icon */}
                    </button>
                  </div>
                </li>
                <div className="tooltip" data-tip="Delete">
                  <li>
                    <button
                      onClick={() => handleDeleteSubtask(subtask.id)}
                      className="btn btn-ghost btn-md text-error p-2 ">
                      <Trash2 /> {/*Delete Icon */}
                    </button>
                  </li>
                </div>
              </ul>
            </div>
          </div>
          <p className="text-gray-600">{subtask.description}</p>
          <p className="text-gray-600">{subtask.parentId}</p>
        </div>
      </div>
    </div>
  );
};
