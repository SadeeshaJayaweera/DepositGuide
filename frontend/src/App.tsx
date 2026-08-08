import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

function Dashboard() {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <p>Welcome to DepositGuide!</p>
    </div>
  );
}

function Statements() {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Statements</h2>
      <p>Your uploaded statements will appear here.</p>
    </div>
  );
}

function Chat() {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Chat</h2>
      <p>Ask questions about your finances.</p>
    </div>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <nav className="w-64 bg-white border-r border-gray-200 p-4">
        <h1 className="text-xl font-bold text-blue-600 mb-8">DepositGuide</h1>
        <ul className="space-y-2">
          <li>
            <Link to="/dashboard" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Dashboard
            </Link>
          </li>
          <li>
            <Link to="/statements" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Statements
            </Link>
          </li>
          <li>
            <Link to="/chat" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Chat
            </Link>
          </li>
        </ul>
      </nav>
      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/statements" element={<Statements />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
