// Function to show/hide navigation menu on mobile devices
document.addEventListener('DOMContentLoaded', function() {
    // Handle closing alert messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Highlight active menu item
    const currentLocation = location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Function to format numbers in currency format
function formatCurrency(amount, currency = '₸') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'KZT',
        minimumFractionDigits: 2
    }).format(amount);
}