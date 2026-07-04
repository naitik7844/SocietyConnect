document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar if clicked outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 992) {
                if (!sidebar.contains(e.target) && sidebar.classList.contains('active')) {
                    sidebar.classList.remove('active');
                }
            }
        });
    }
});
