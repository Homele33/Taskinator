import { Subtask } from "./tasksTypes";
import { Pencil, Trash2, Check, EllipsisVertical } from "lucide-react";
import { deleteSubtask, toggleSubtask } from "@/utils/taskUtils";

interface SubtaskCardProps {
  subtask: Subtask;
  parentId: string;
  isDone: boolean;
  onRefresh: () => void;
  onEdit: (subtask: Subtask, parentId: string) => void;
}

export const SubtaskCard: React.FC<SubtaskCardProps> = ({
  subtask,
  onEdit,
  onRefresh,
  parentId,
}) => {
  const handleDeleteSubtask = async (id: string) => {
    await deleteSubtask(parentId, id);
    onRefresh();
  };


  const handleComplete = async (id: string) => {
    await toggleSubtask(parentId, id);
    onRefresh();
  };

  return (
    <div>
      <div
        className={`card scale-90  ${subtask.isDone ? "bg-success" : "bg-base-300"}`}
        data-testid={`subtask-card-${subtask.id}`}
      >
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <h2
                className="text-lg font-bold text-primary"
                data-testid={`subtask-title-${subtask.id}`}
              >
                {subtask.title}
              </h2>
            </div>

            <div className="">
              <div
                className="tooltip"
                data-tip={subtask.isDone ? "Uncomplete" : "Complete"}
              >
                <button
                  onClick={() => handleComplete(subtask.id)}
                  className={`btn btn-ghost btn-md ${subtask.isDone ? "text-error" : "text-green-500"
                    }`}
                  data-testid={`subtask-complete-toggle-${subtask.id}`}
                >
                  <Check />
                </button>
              </div>
              <div className="dropdown dropdown-top z-100" data-testid={`subtask-menu-button-${subtask.id}`}>
                <label tabIndex={0} className="text-primary">
                  <EllipsisVertical />
                </label>
                <ul
                  tabIndex={0}
                  className=" p-2 shadow dropdown-content menu bg-accent-content rounded-box"
                >
                  <div className="tooltip" data-tip="Edit subtask">
                    <li>
                      <button
                        onClick={() => onEdit(subtask, parentId)}
                        className="btn btn-ghost btn-md text-yellow-400"
                        data-testid={`subtask-edit-button-${subtask.id}`}
                      >
                        <Pencil /> {/* Edit icon */}
                      </button>
                    </li>
                  </div>

                  <div className="tooltip" data-tip="Delete">
                    <li>
                      <button
                        onClick={() => handleDeleteSubtask(subtask.id)}
                        className="btn btn-ghost btn-md text-error"
                        data-testid={`subtask-delete-button-${subtask.id}`}
                      >
                        <Trash2 /> {/*Delete Icon */}
                      </button>
                    </li>
                  </div>
                </ul>
              </div>
            </div>
          </div>
          <p className="text-gray-600">{subtask.description}</p>
        </div>
      </div>
    </div>
  );
};
