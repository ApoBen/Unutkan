import 'package:flutter/material.dart';
import 'cleaner_screen.dart';
import 'shredder_screen.dart';
import 'sanitizer_screen.dart';
import 'vault_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 36.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 20),
              // Logo
              Center(
                child: CustomPaint(
                  size: const Size(80, 80),
                  painter: LogoPainter(),
                ),
              ),
              const SizedBox(height: 16),
              // Title
              const Text(
                'unutkan',
                style: TextStyle(
                  fontFamily: 'Space Grotesk',
                  fontSize: 36,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                  letterSpacing: -1.0,
                ),
              ),
              const SizedBox(height: 8),
              // Subtitle
              const Text(
                'Kişisel veri güvenliğinizi artıran dijital hijyen araç kutusu.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 13,
                  color: Color(0xFFB3B3B3),
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 48),
              // Grid of cards
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 0.9,
                children: [
                  _buildToolCard(
                    context,
                    title: 'Metadata Temizleyici',
                    description: 'Dosyalardaki konum, kamera, yazar bilgilerini temizler.',
                    iconChar: 'MT',
                    color: const Color(0xFF3584E4),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const CleanerScreen()),
                    ),
                  ),
                  _buildToolCard(
                    context,
                    title: 'Güvenli Silici',
                    description: 'Dosyaları diske rastgele veri yazarak kalıcı imha eder.',
                    iconChar: 'GS',
                    color: const Color(0xFFF66151),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const ShredderScreen()),
                    ),
                  ),
                  _buildToolCard(
                    context,
                    title: 'Metin Arındırıcı',
                    description: 'Hassas verileri maskeler, link takip kodlarını temizler.',
                    iconChar: 'MA',
                    color: const Color(0xFF1CA8A3),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SanitizerScreen()),
                    ),
                  ),
                  _buildToolCard(
                    context,
                    title: 'Geçici Bellek Kasası',
                    description: 'Hassas şifre ve dosyaları sadece RAM üzerinde saklar.',
                    iconChar: 'GB',
                    color: const Color(0xFF2EC27E),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const VaultScreen()),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildToolCard(
    BuildContext context, {
    required String title,
    required String description,
    required String iconChar,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF303030),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    iconChar,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            const Spacer(),
            Text(
              title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              description,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 10.5,
                color: Colors.white.withOpacity(0.6),
                height: 1.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class LogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..isAntiAlias = true
      ..style = PaintingStyle.fill;

    final w = size.width;
    final h = size.height;

    // Shield gradient
    final path = Path()
      ..moveTo(w / 2, 6)
      ..lineTo(w - 12, 18)
      ..quadraticBezierTo(w - 12, h - 32, w / 2, h - 8)
      ..quadraticBezierTo(12, h - 32, 12, 18)
      ..close();

    final gradient = LinearGradient(
      colors: const [Color(0xFF3584E4), Color(0xFF1C51A3)],
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
    );

    paint.shader = gradient.createShader(Offset.zero & size);
    canvas.drawPath(path, paint);

    // Inner lock
    final pen = Paint()
      ..color = Colors.white
      ..strokeWidth = 3.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final arcRect = Rect.fromLTWH(w / 2 - 10, h / 2 - 16, 20, 18);
    canvas.drawArc(arcRect, 3.14, 3.14, false, pen);
    canvas.drawLine(Offset(w / 2 - 10, h / 2 - 7), Offset(w / 2 - 10, h / 2 - 1), pen);

    final fillPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;
    canvas.drawRect(Rect.fromLTWH(w / 2 - 13, h / 2 - 1, 26, 19), fillPaint);

    final holePaint = Paint()
      ..color = const Color(0xFF1C51A3)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(w / 2, h / 2 + 7), 3, holePaint);

    final keyLinePaint = Paint()
      ..color = const Color(0xFF1C51A3)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    canvas.drawLine(Offset(w / 2, h / 2 + 10), Offset(w / 2, h / 2 + 15), keyLinePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
