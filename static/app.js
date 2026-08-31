document.addEventListener('DOMContentLoaded', () => {
  const taskList = document.getElementById('task-list');
  const addTaskForm = document.getElementById('add-task-form');
  const taskInput = document.getElementById('task-input');

  // Fetch and display tasks
  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/tasks');
      const tasks = await response.json();
      renderTasks(tasks);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  // Render tasks into the DOM
  const renderTasks = (tasks) => {
    taskList.innerHTML = '';
    tasks.forEach(task => {
      const li = document.createElement('li');
      li.textContent = task.title;
      if (task.completed) {
        li.classList.add('completed');
      }
      taskList.appendChild(li);
    });
  };

  // Handle form submission to add a new task
  addTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = taskInput.value.trim();
    if (!title) return;

    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      });
      if (response.ok) {
        taskInput.value = '';
        fetchTasks(); // Refresh the list
      } else {
        console.error('Failed to add task');
      }
    } catch (error) {
      console.error('Error adding task:', error);
    }
  });

  // Initial load
  fetchTasks();
});
