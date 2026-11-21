// The board's state that is the browser's own and that the server renders: the folded columns, the
// folded sidebar, the panel's width. One cookie for the device, `lem_board`, a JSON object written
// URL-encoded, SameSite=Lax, for every page of the server, kept a year. The server reads it at each
// request, so the first paint is right and a morph keeps what the owner chose.
const NAME = 'lem_board';

export function read() {
  const found = document.cookie.split('; ').find(part => part.startsWith(`${NAME}=`));
  try {
    const value = found ? JSON.parse(decodeURIComponent(found.slice(NAME.length + 1))) : {};
    return value && typeof value === 'object' ? value : {};
  } catch {
    return {};
  }
}

export function write(change) {
  const value = {...read(), ...change};
  document.cookie = `${NAME}=${encodeURIComponent(JSON.stringify(value))}; Path=/; Max-Age=31536000; SameSite=Lax`;
  return value;
}
