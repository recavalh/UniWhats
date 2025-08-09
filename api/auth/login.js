export default function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const { email, password } = req.body || {};

  const users = {
    'admin@school.com': { name: 'João Diretor', role: 'Manager', password: 'admin123' },
    'maria@school.com': { name: 'Maria Silva', role: 'Receptionist', password: 'maria123' },
    'carlos@school.com': { name: 'Carlos Souza', role: 'Coordinator', password: 'carlos123' },
    'ana@school.com': { name: 'Ana Costa', role: 'Sales Rep', password: 'ana123' },
  };

  const user = users[email];
  if (!user || user.password !== password) {
    return res.status(401).json({ detail: 'Invalid credentials' });
  }

  return res.status(200).json({
    token: `mocktoken-${email}`,
    user: { email, name: user.name, role: user.role },
  });
}
