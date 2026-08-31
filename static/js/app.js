// static/js/app.js
// Frontend logic for product listing and cart management

const API_BASE = '/api';

const state = {
  products: [],
  cart: JSON.parse(localStorage.getItem('cart') || '[]'),
};

// DOM refs
const productContainer = document.getElementById('product-list');
const cartContainer = document.getElementById('cart-items');
const cartToggleBtn = document.getElementById('cart-toggle');
const cartPanel = document.getElementById('cart-panel');

// Fetch products
async function fetchProducts() {
  try {
    const response = await fetch(`${API_BASE}/products`);
    if (!response.ok) throw new Error('Failed to load products');
    const products = await response.json();
    state.products = products;
    renderProducts();
  } catch (error) {
    console.error('Error fetching products:', error);
    productContainer.innerHTML = '<p>Failed to load products. Please try again later.</p>';
  }
}

// Render product list
function renderProducts() {
  if (!productContainer) return;
  if (state.products.length === 0) {
    productContainer.innerHTML = '<p>No products available.</p>';
    return;
  }
  productContainer.innerHTML = state.products.map(product => `
    <div class="product" data-id="${product.id}">
      <h3>${product.name}</h3>
      <p>${product.description || ''}</p>
      <p class="price">$${(product.price || 0).toFixed(2)}</p>
      <button class="add-to-cart" data-id="${product.id}">Add to Cart</button>
    </div>
  `).join('');
}

// Cart display (localStored)
function renderCart() {
  if (!cartContainer) return;
  if (state.cart.length === 0) {
    cartContainer.innerHTML = '<p>Your cart is empty.</p>';
    return;
  }
  const total = state.cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  cartContainer.innerHTML = `
    <ul>
      ${state.cart.map(item => `
        <li>
          ${item.name} x ${item.quantity} - $${(item.price * item.quantity).toFixed(2)}
          <button class="remove-from-cart" data-id="${item.id}">Remove</button>
        </li>
      `).join('')}
    </ul>
    <p><strong>Total: $${total.toFixed(2)}</strong></p>
  `;
}

// Add to cart
function addToCart(productId) {
  const product = state.products.find(p => p.id === productId);
  if (!product) return;
  const existing = state.cart.find(item => item.id === productId);
  if (existing) {
    existing.quantity += 1;
  } else {
    state.cart.push({ ...product, quantity: 1 });
  }
  localStorage.setItem('cart', JSON.stringify(state.cart));
  renderCart();
}

// Remove from cart
function removeFromCart(productId) {
  state.cart = state.cart.filter(item => item.id !== productId);
  localStorage.setItem('cart', JSON.stringify(state.cart));
  renderCart();
}

// Toggle cart panel
function toggleCart() {
  if (cartPanel) {
    const isHidden = cartPanel.classList.toggle('hidden');
    cartToggleBtn.textContent = isHidden ? 'Show Cart' : 'Hide Cart';
  }
}

// Event delegation for product actions
if (productContainer) {
  productContainer.addEventListener('click', (e) => {
    if (e.target.classList.contains('add-to-cart')) {
      const id = parseInt(e.target.dataset.id, 10);
      addToCart(id);
    }
  });
}

// Event delegation for cart actions
if (cartContainer) {
  cartContainer.addEventListener('click', (e) => {
    if (e.target.classList.contains('remove-from-cart')) {
      const id = parseInt(e.target.dataset.id, 10);
      removeFromCart(id);
    }
  });
}

// Cart toggle
if (cartToggleBtn) {
  cartToggleBtn.addEventListener('click', toggleCart);
}

// Initial render
fetchProducts();
renderCart();
