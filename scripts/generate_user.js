const timestamp = Date.now();
const suffix = String(timestamp).slice(-8)

// ini kenapa bisa date.now kemudian variabel output akan mengenerate sesuai dengan waktu generate jadi usernya beda beda
output.email = `user_${timestamp}@example.com`;
output.password = `angka_${timestamp}`;
output.username = `user_${timestamp}`;
output.reference = `REF${timestamp}`;
output.phone = `0812${suffix}`;
output.customerId = `CUST${String(timestamp).slice(-6)}`;



/*const timestamp = Date.now();

output.email = `qa_${timestamp}@mail.com`;
output.phone = `0812${String(timestamp).slice(-8)}`;
output.customerId = `CUST${String(timestamp).slice(-6)}`;
output.reference = `TRX${timestamp}`;
*/

// generator yang berguna saat real projek

