import React from "react";
import { Home, Settings, Calendar, LogOutIcon } from "lucide-react";
import Link from "next/link";
import { logoutUser } from "@/firebase/firebaseClient";
import { useRouter } from "next/router";

// Define menu item type
interface MenuItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

// Define props for the component
interface BurgerMenuProps {
  className?: string;
}

const BurgerMenu: React.FC<BurgerMenuProps> = ({ className = "" }) => {
  // Define menu items
  const router = useRouter();
  const menuItems: MenuItem[] = [
    {
      name: "Home",
      path: "/",
      icon: <Home size={20} />,
    },
    {
      name: "Calendar",
      path: "/calendar",
      icon: <Calendar size={20} />,
    },
    {
      name: "Settings",
      path: "/settings",
      icon: <Settings size={20} />,
    },
  ];

  return (
    <div className={`fixed top-4 left-4 z-50 ${className}`}>
      {/* Using DaisyUI dropdown component */}
      <div className="dropdown" data-testid="burger-menu">
        {/* Burger button as dropdown trigger */}
        <label tabIndex={0} className="btn btn-ghost btn-circle text-primary">
          <div className="w-6 flex flex-col gap-1">
            <span className="block h-0.5 w-full bg-current"></span>
            <span className="block h-0.5 w-full bg-current"></span>
            <span className="block h-0.5 w-full bg-current"></span>
          </div>
        </label>

        {/* Dropdown menu */}
        <ul
          tabIndex={0}
          className="dropdown-content menu menu-sm z-[1] mt-3 p-2 shadow bg-base-100 rounded-box w-52"
        >
          {menuItems.map((item) => (
            <li key={item.path}>
              <Link href={item.path} className="flex items-center gap-2">
                <span className="text-primary">{item.icon}</span>
                <span className="text-accent">{item.name}</span>
              </Link>
            </li>
          ))}
          <li>
            <button
              className="btn gap-2 bg-base-100 btn-ghost text-error"
              onClick={() => {
                logoutUser().then(() => {
                  router.push("/login");
                });
              }}
              data-testid="logout-button"
            >
              {" "}
              <LogOutIcon size={20} />
              Logout
            </button>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default BurgerMenu;
