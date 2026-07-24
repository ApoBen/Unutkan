import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(const UnutkanApp());
}

class UnutkanApp extends StatelessWidget {
  const UnutkanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Unutkan',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF3584E4),
        scaffoldBackgroundColor: const Color(0xFF1E1E1E),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3584E4),
          secondary: Color(0xFF2EC27E),
          error: Color(0xFFF66151),
          background: Color(0xFF1E1E1E),
          surface: Color(0xFF303030),
        ),
        fontFamily: 'Cantarell',
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Colors.white),
        ),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}
