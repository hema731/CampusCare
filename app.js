
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.flash').forEach(el=>{
    setTimeout(()=>{el.style.transition='opacity .45s';el.style.opacity='0';setTimeout(()=>el.remove(),500)},5200);
  });
  document.querySelectorAll('.table-search').forEach(input=>{
    input.addEventListener('input',()=>{
      const query=input.value.trim().toLowerCase();
      const rows=document.querySelectorAll('tbody tr');
      rows.forEach(row=>{row.hidden=!row.innerText.toLowerCase().includes(query);});
    });
  });
});
