document.addEventListener('DOMContentLoaded', function(){
  var reveals = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  function onScroll(){
    reveals.forEach(function(el){
      var rect = el.getBoundingClientRect();
      if(rect.top < window.innerHeight - 80) el.classList.add('active');
    });
  }
  onScroll();
  window.addEventListener('scroll', onScroll, {passive:true});
});
