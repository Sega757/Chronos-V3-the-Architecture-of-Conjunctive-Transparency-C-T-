export async function fetchArticles() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api'}/articles`);
  return res.json();
}
