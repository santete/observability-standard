using ISC.Observability.Extensions;

var builder = WebApplication.CreateBuilder(args);

// Gắn SDK Observability như bình thường
builder.AddStandardObservability("MiddlewarePoC");

var app = builder.Build();

// Gắn middleware SDK
app.UseStandardObservability();

// ============================================================
// CASE 1: API bình thường - trả về response tùy ý của Dev
// ============================================================
app.MapGet("/healthy", () => Results.Ok(new
{
    status = "OK",
    message = "Dev tự quyết response, SDK không can thiệp"
}));

// ============================================================
// CASE 2: API throw exception - kiểm tra SDK có nuốt response không
// ============================================================
app.MapGet("/crash", () =>
{
    throw new InvalidOperationException("Lỗi nghiệp vụ do Dev tự throw để test");
});

// ============================================================
// CASE 3: API có Exception Handler riêng của Dev
// Dev tự bắt exception và trả về response theo format riêng
// ============================================================
app.MapGet("/handled-crash", () =>
{
    try
    {
        throw new ArgumentException("Lỗi validate input từ user");
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new
        {
            errorCode = "VALIDATION_FAILED",
            message = ex.Message,
            devNote = "Response này do Dev tự xử lý, SDK không đè lên"
        });
    }
});

Console.WriteLine(@"
=====================================================
  MIDDLEWARE PoC - CHỨNG MINH SDK KHÔNG NUỐT RESPONSE  
=====================================================

Mở browser hoặc dùng curl để test 3 endpoint:

  1. GET http://localhost:5199/healthy
     -> Kỳ vọng: Trả JSON bình thường do Dev quyết định

  2. GET http://localhost:5199/crash
     -> Kỳ vọng: ASP.NET Core trả mặc định (500 HTML error page)
        SDK CHỈ ghi log + trace, KHÔNG đè response

  3. GET http://localhost:5199/handled-crash
     -> Kỳ vọng: Trả JSON 400 do Dev tự bắt và format
        SDK KHÔNG can thiệp gì cả

=====================================================
");

app.Run("http://localhost:5199");
