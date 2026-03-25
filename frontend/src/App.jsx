import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [message, setMessage] = useState('')

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const url = isLogin ? 'http://localhost:5000/login' : 'http://localhost:5000/register'
      const payload = isLogin ? { username: formData.username, password: formData.password } : formData
      const response = await axios.post(url, payload)
      setMessage(response.data.message || 'Success')
      if (isLogin && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token)
        setMessage('Logged in successfully')
      }
    } catch (error) {
      setMessage(error.response?.data?.message || 'Error occurred')
    }
  }

  return (
    <div className="App">
      <h1>{isLogin ? 'Login' : 'Register'}</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="username"
          placeholder="Username"
          value={formData.username}
          onChange={handleChange}
          required
        />
        {!isLogin && (
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        )}
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
      </form>
      <p>{message}</p>
      <button onClick={() => setIsLogin(!isLogin)}>
        Switch to {isLogin ? 'Register' : 'Login'}
      </button>
    </div>
  )
}

export default App