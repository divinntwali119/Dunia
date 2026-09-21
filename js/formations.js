document.addEventListener('DOMContentLoaded', function(){
  var filterBtns = document.querySelectorAll('.filter-btn');
  var cards = document.querySelectorAll('.formation-card');
  filterBtns.forEach(function(btn){
    btn.addEventListener('click', function(){
      var cat = btn.getAttribute('data-category');
      filterBtns.forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      cards.forEach(function(card){
        if(cat==='all' || card.getAttribute('data-category')===cat) card.style.display=''; else card.style.display='none';
      });
    });
  });

  var searchForm = document.getElementById('searchForm');
  var searchInput = document.getElementById('searchInput');
  if(searchForm && searchInput){
    searchForm.addEventListener('submit', function(e){
      e.preventDefault();
      var q = (searchInput.value||'').toLowerCase().trim();
      var count = 0;
      cards.forEach(function(card){
        var title = card.getAttribute('data-title')||'';
        var desc = card.getAttribute('data-description')||'';
        if(q==='' || title.toLowerCase().includes(q) || desc.toLowerCase().includes(q)) { card.style.display=''; count++; }
        else card.style.display='none';
      });
      document.getElementById('resultCount').textContent = count;
    });
  }
});
