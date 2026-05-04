import Login from "./pages/Login";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";

function App() {
  const token = localStorage.getItem("token");

  if (!token) return <Login />;

  const path = window.location.pathname;

  if (path === "/dashboard") return <Dashboard />;

  return <Chat />;
}

export default App;
