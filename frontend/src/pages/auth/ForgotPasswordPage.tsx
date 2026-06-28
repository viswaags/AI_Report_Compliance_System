import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useForgotPassword } from '@/hooks/useAuth';

const forgotPasswordSchema = z.object({
  email: z.string().email('Invalid email address'),
});

type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const forgotPassword = useForgotPassword();

  const form = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordForm) => {
    setError(null);
    try {
      await forgotPassword.mutateAsync(data.email);
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email. Please try again.');
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30 px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
              <Mail className="h-7 w-7 text-primary" />
            </div>
            <CardTitle>Check your email</CardTitle>
            <CardDescription>
              If the account exists, a reset token was sent to {form.getValues('email')}.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center text-sm text-muted-foreground">
            <p>
              Didn't receive the email? Check your spam folder, then{' '}
              <button
                onClick={() => setSubmitted(false)}
                className="text-primary hover:underline"
              >
                try another email
              </button>
            </p>
          </CardContent>
          <CardFooter>
            <Link to="/auth/login" className="w-full">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to sign in
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle>Forgot password?</CardTitle>
          <CardDescription>
            Enter your email address and we'll send you a link to reset your password.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="Enter your email"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" className="w-full" disabled={forgotPassword.isPending}>
                {forgotPassword.isPending ? 'Sending...' : 'Send reset link'}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter>
          <Link to="/auth/login" className="w-full">
            <Button variant="ghost" className="w-full">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to sign in
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}

export default ForgotPasswordPage;
