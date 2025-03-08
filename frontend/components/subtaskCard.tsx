import { Subtask } from "./task";
import { Pencil, Trash2, Check, Menu } from "lucide-react";

interface SubtaskCardProps {
  subtask: Subtask;
  parentId: string;
  isDone: boolean;
  onRefresh: () => void;
}

// const getCardStyles = (isDone: boolean) => {
//   const className = "card hover:shadow-xl scale-90 opacity-90";
//   if (!isDone) {
//     return `${className}  bg-primary `;
//   }
//   return `${className} bg-green-900 `;
// };

export const SubtaskCard: React.FC<SubtaskCardProps> = ({
  subtask,

  onRefresh,
  parentId,
}) => {
  const handleDeleteSubtask = async (id: string) => {
    const response = await fetch(
      `http://localhost:5000/api/tasks/subtasks/${parentId}/${id}`,
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

  const handleComplete = async (id: string) => {
    const response = await fetch(
      `http://localhost:5000/api/${parentId}/${id}/toggle_subtask`,
      {
        method: "PATCH",
      }
    );
    if (!response.ok) {
      throw new Error("Failed to toggle subtask");
    }
    onRefresh();
  };

  return (
    <div>
      <div
        className={`card scale-90  ${
          subtask.isDone ? "bg-success-content" : "bg-primary-content"
        }`}>
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold">{subtask.title}</h2>
            </div>

            <div className="">
              <div className="tooltip" data-tip="Complete">
                <button
                  onClick={() => handleComplete(subtask.id)}
                  className={`btn btn-ghost btn-md ${
                    subtask.isDone ? "text-error" : "text-green-500"
                  }`}>
                  <Check />
                </button>
              </div>
              <div className="dropdown dropdown-top z-100">
                <label tabIndex={0}>
                  <Menu />
                </label>
                <ul
                  tabIndex={0}
                  className=" p-2 shadow dropdown-content menu bg-base-100 rounded-box">
                  <div className="tooltip" data-tip="Edit subtask">
                    <li>
                      <button
                        onClick={() => handleEditSubtask(subtask)}
                        className="btn btn-ghost btn-md text-yellow-400">
                        <Pencil /> {/* Edit icon */}
                      </button>
                    </li>
                  </div>

                  <div className="tooltip" data-tip="Delete">
                    <li>
                      <button
                        onClick={() => handleDeleteSubtask(subtask.id)}
                        className="btn btn-ghost btn-md text-error">
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
