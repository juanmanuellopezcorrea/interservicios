# Deployment Guide - Vercel

## Prerequisites

- GitHub repository connected to Vercel
- Supabase project configured with database
- Environment variables configured in Vercel

## Environment Variables Required

Add these to your Vercel project settings (Settings > Environment Variables):

```
POSTGRES_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here
MAIL_ADMIN_REPORT_TO=admin@example.com
```

## Database Setup

The application uses PostgreSQL via Supabase. Tables are automatically created on deployment.

### Tables Created:
- `usuarios` - User management
- `clientes` - Clients
- `trabajadores` - Workers
- `tareas` - Tasks
- `registro_hora` - Time tracking
- `ficaje_control_horario` - Time control
- `timer_trabajo` - Work timers
- `plantilla_tarea` - Task templates
- `catalogo_obligaciones_legacy` - Compliance obligations
- `obligacion_cliente_legacy` - Client obligations
- `solicitud_presupuesto` - Budget requests
- `cuestionario_normativo_cliente` - Compliance questionnaires

## Default Credentials

After deployment, the app creates a default admin user:
- **Username:** admin
- **Password:** admin

**Change this password immediately after first login!**

## Deployment Steps

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Vercel will automatically:**
   - Build the application
   - Install dependencies from `requirements.txt`
   - Run `vercel_init.py` for database setup
   - Deploy to production

3. **Monitor deployment**
   - Check Vercel dashboard for build logs
   - Visit your app URL to verify it's running

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export SECRET_KEY=dev-secret-key

# Run application
python app.py
```

The app will use SQLite locally and PostgreSQL when deployed to Vercel.

## Troubleshooting

### "Internal Server Error"
- Check Vercel logs: `vercel logs`
- Verify POSTGRES_URL is correct
- Check database connection permissions

### Static files not loading
- Ensure `static/` directory exists
- Check `vercel.json` routes configuration

### Admin user not created
- Check database connection
- Verify migrations ran successfully
- Check `vercel_init.py` logs in Vercel dashboard

## Support

For issues, check:
- Vercel dashboard logs
- Application logs with `vercel logs`
- Supabase dashboard for database status
