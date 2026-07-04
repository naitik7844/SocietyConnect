document.addEventListener('DOMContentLoaded', function() {
    // 1. Alerts Close Handler
    const alertCloses = document.querySelectorAll('.alert-close');
    alertCloses.forEach(btn => {
        btn.addEventListener('click', function() {
            const alert = btn.closest('.alert');
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    });

    // 2. Simple Modal Handler
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    };

    // Close modal when clicking outside content area
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});
