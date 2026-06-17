import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User as UserIcon, UserPlus } from 'lucide-react';
import { toast } from 'sonner';
import AuthLayout from '../components/AuthLayout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api/http';

/** Lightweight password strength meter (length + character variety). */
function strength(pw: string): { score: number; label: string; tone: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const levels = [
    { label: 'Too short', tone: 'bg-rose-500' },
    { label: 'Weak', tone: 'bg-rose-500' },
    { label: 'Fair', tone: 'bg-amber-500' },
    { label: 'Good', tone: 'bg-accent-500' },
    { label: 'Strong', tone: 'bg-emerald-500' },
    { label: 'Excellent', tone: 'bg-emerald-600' },
  ];
  return { score, ...levels[Math.min(score, levels.length - 1)] };
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const pwStrength = useMemo(() => strength(password), [password]);
  const canSubmit = email && password.length >= 8;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await register(email, password, name || undefined);
      toast.success(`Account created — welcome, ${user.name || user.email}`);
      navigate('/', { replace: true });
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.code === 'REGISTRATION_CLOSED'
            ? 'Registration is restricted to approved email domains. Contact an administrator for access.'
            : err.code === 'EMAIL_TAKEN'
              ? 'An account with this email already exists. Try signing in instead.'
              : err.message
          : 'Could not create the account. Please try again.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join the curation workspace."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-primary-600 hover:text-primary-700">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          name="name"
          label="Full name"
          placeholder="Jane Curator"
          autoComplete="name"
          leftIcon={<UserIcon className="h-4 w-4" />}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          name="email"
          type="email"
          label="Email"
          placeholder="you@institution.org"
          autoComplete="email"
          required
          leftIcon={<Mail className="h-4 w-4" />}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          hint="Must be an approved institutional domain."
        />
        <div>
          <Input
            name="password"
            type="password"
            label="Password"
            placeholder="At least 8 characters"
            autoComplete="new-password"
            required
            minLength={8}
            leftIcon={<Lock className="h-4 w-4" />}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {password && (
            <div className="mt-2 flex items-center gap-2">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all ${pwStrength.tone}`}
                  style={{ width: `${(pwStrength.score / 5) * 100}%` }}
                />
              </div>
              <span className="w-16 text-right text-xs font-medium text-slate-500">
                {pwStrength.label}
              </span>
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
            {error}
          </div>
        )}

        <Button
          type="submit"
          className="w-full"
          loading={submitting}
          disabled={!canSubmit}
          icon={<UserPlus className="h-4 w-4" />}
        >
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}
